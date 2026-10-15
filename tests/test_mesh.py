from datetime import datetime

import pytest

import schemas
from mesh import LocalTransport, ServiceMesh, Transport, build_local_mesh
from services import SERVICE_CLASSES, NotFoundError


class RecordingTransport(Transport):
    """
    Wraps another transport and records every call routed through it.
    """

    def __init__(self, inner: Transport):
        self.inner = inner
        self.calls = []

    def call(self, service, method, *args, **kwargs):
        self.calls.append((service, method))
        return self.inner.call(service, method, *args, **kwargs)


@pytest.fixture
def recording_mesh(db, db_user):
    mesh = ServiceMesh(user_id=db_user.id)
    services = {cls.name: cls(db=db, user_id=db_user.id, mesh=mesh) for cls in SERVICE_CLASSES}
    transport = RecordingTransport(LocalTransport(services))
    mesh.connect(transport)
    return mesh, transport


def test_mesh_routes_to_service_and_persists(mesh):
    meeting = mesh.meetings.create(
        schemas.MeetingCreate(title="Standup", scheduled_time=datetime(2024, 1, 15, 10))
    )

    assert mesh.meetings.get(meeting.id).title == "Standup"


def test_mesh_is_bound_to_user(db):
    mesh = build_local_mesh(db, user_id=42)

    assert mesh.user_id == 42


def test_inter_service_calls_go_through_mesh(recording_mesh):
    mesh, transport = recording_mesh
    meeting = mesh.meetings.create(
        schemas.MeetingCreate(title="Standup", scheduled_time=datetime(2024, 1, 15, 10))
    )
    transport.calls.clear()

    mesh.notes.create(schemas.NoteCreate(content="hi", meeting_id=meeting.id))

    assert transport.calls == [("notes", "create"), ("meetings", "get")]


def test_service_errors_propagate_through_mesh(mesh):
    with pytest.raises(NotFoundError):
        mesh.meetings.get(99)


def test_unknown_service_raises(mesh):
    with pytest.raises(AttributeError):
        mesh.unknown.get(1)


def test_mesh_without_transport_raises():
    with pytest.raises(RuntimeError):
        ServiceMesh(user_id=1).users.list()
