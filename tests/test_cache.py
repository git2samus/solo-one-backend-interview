from datetime import datetime

import pytest

import models
import schemas
from cache import InMemoryCache, cache_policy, cached
from mesh import CachingTransport, LocalTransport, ServiceMesh, Transport, build_local_mesh
from services import SERVICE_CLASSES


class CountingTransport(Transport):
    """
    Wraps another transport and records every call that reaches it.
    """

    def __init__(self, inner: Transport):
        self.inner = inner
        self.calls = []

    def call(self, service, method, *args, **kwargs):
        self.calls.append((service, method))
        return self.inner.call(service, method, *args, **kwargs)


@pytest.fixture
def cache():
    return InMemoryCache()


@pytest.fixture
def make_mesh(db, cache):
    """
    Build a caching mesh for a user; returns (mesh, calls that missed the cache).
    """

    def make(user_id):
        mesh = ServiceMesh(user_id)
        services = {cls.name: cls(db=db, user_id=user_id, mesh=mesh) for cls in SERVICE_CLASSES}
        backend = CountingTransport(LocalTransport(services))
        mesh.connect(CachingTransport(backend, cache, user_id, cache_policy(SERVICE_CLASSES)))
        return mesh, backend.calls

    return make


@pytest.fixture
def make_user(db):
    def make(name):
        user = models.User(name=name, email=f"{name.lower()}@example.com")
        db.add(user)
        db.commit()
        return user.id

    return make


@pytest.fixture
def alice(make_user):
    return make_user("Alice")


@pytest.fixture
def bob(make_user):
    return make_user("Bob")


def new_meeting(attendee_ids=()):
    return schemas.MeetingCreate(
        title="Standup", scheduled_time=datetime(2024, 1, 15, 10), attendee_ids=list(attendee_ids)
    )


def test_repeated_read_is_served_from_cache(make_mesh, alice):
    mesh, calls = make_mesh(alice)
    meeting = mesh.meetings.create(new_meeting())
    calls.clear()

    first = mesh.meetings.get(meeting.id)
    second = mesh.meetings.get(meeting.id)

    assert first == second
    assert calls == [("meetings", "get")]


def test_cache_persists_across_meshes_of_the_same_user(make_mesh, alice):
    mesh, _ = make_mesh(alice)
    mesh.meetings.list()

    other_request_mesh, calls = make_mesh(alice)
    other_request_mesh.meetings.list()

    assert calls == []


def test_entries_are_per_user(make_mesh, alice, bob):
    alice_mesh, _ = make_mesh(alice)
    meeting = alice_mesh.meetings.create(new_meeting())
    assert [m.id for m in alice_mesh.meetings.list()] == [meeting.id]

    bob_mesh, calls = make_mesh(bob)

    assert bob_mesh.meetings.list() == []
    assert calls == [("meetings", "list")]


def test_arguments_are_part_of_the_key(make_mesh, alice):
    mesh, calls = make_mesh(alice)
    meeting = mesh.meetings.create(new_meeting())
    mesh.tasks.create(schemas.TaskCreate(title="t", due_meeting_id=meeting.id))
    calls.clear()

    assert len(mesh.tasks.list(status="pending")) == 1
    assert mesh.tasks.list(status="completed") == []
    assert calls.count(("tasks", "list")) == 2


def test_write_invalidates_reads_of_the_same_service(make_mesh, alice):
    mesh, _ = make_mesh(alice)
    assert mesh.meetings.list() == []

    meeting = mesh.meetings.create(new_meeting())

    assert [m.id for m in mesh.meetings.list()] == [meeting.id]


def test_write_invalidates_reads_that_declared_the_service(make_mesh, alice):
    mesh, _ = make_mesh(alice)
    meeting = mesh.meetings.create(new_meeting())
    assert mesh.meetings.get(meeting.id).notes == []

    mesh.notes.create(schemas.NoteCreate(content="hi", meeting_id=meeting.id))

    assert [n.content for n in mesh.meetings.get(meeting.id).notes] == ["hi"]


def test_write_invalidates_reads_that_called_the_service_through_the_mesh(make_mesh, alice, bob):
    alice_mesh, _ = make_mesh(alice)
    bob_mesh, _ = make_mesh(bob)
    assert [u.id for u in bob_mesh.users.list()] == [bob]

    alice_mesh.meetings.create(new_meeting(attendee_ids=[bob]))

    assert [u.id for u in bob_mesh.users.list()] == [alice, bob]


def test_write_invalidates_other_users_entries(make_mesh, alice, bob):
    alice_mesh, _ = make_mesh(alice)
    bob_mesh, _ = make_mesh(bob)
    meeting = alice_mesh.meetings.create(new_meeting(attendee_ids=[bob]))
    assert bob_mesh.meetings.get(meeting.id).title == "Standup"

    alice_mesh.meetings.update(meeting.id, schemas.MeetingUpdate(title="Retro"))

    assert bob_mesh.meetings.get(meeting.id).title == "Retro"


def test_nested_cache_hits_still_record_dependencies(make_mesh, alice):
    mesh, _ = make_mesh(alice)
    meeting = mesh.meetings.create(new_meeting())
    mesh.meetings.accessible_ids()  # cached before notes.list reads it
    assert mesh.notes.list() == []
    mesh.notes.create(schemas.NoteCreate(content="hi", meeting_id=meeting.id))
    assert len(mesh.notes.list()) == 1

    mesh.meetings.delete(meeting.id)

    assert mesh.notes.list() == []


def test_errors_are_not_cached(make_mesh, alice):
    mesh, calls = make_mesh(alice)

    for _ in range(2):
        with pytest.raises(Exception):
            mesh.meetings.get(99)

    assert calls == [("meetings", "get"), ("meetings", "get")]


def test_cached_values_cannot_be_mutated_by_callers(make_mesh, alice):
    mesh, _ = make_mesh(alice)
    meeting = mesh.meetings.create(new_meeting())

    mesh.meetings.get(meeting.id).title = "Mutated"

    assert mesh.meetings.get(meeting.id).title == "Standup"


def test_result_computed_before_an_invalidation_is_not_stored(cache):
    version = cache.version()
    cache.invalidate({"meetings"})

    cache.set("key", "stale", frozenset({"meetings"}), version)

    assert cache.get("key") is None


def test_cache_policy_includes_own_service_and_declared_reads():
    class Service:
        name = "things"

        @cached
        def get(self):
            ...

        @cached(reads=("others",))
        def list(self):
            ...

        def create(self):
            ...

    assert cache_policy([Service]) == {
        ("things", "get"): frozenset({"things"}),
        ("things", "list"): frozenset({"things", "others"}),
    }


def test_mesh_can_be_built_without_cache(db, alice):
    mesh = build_local_mesh(db, alice, cache=None)

    assert mesh.meetings.list() == []
