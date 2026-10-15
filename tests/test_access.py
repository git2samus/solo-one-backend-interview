import pytest


@pytest.fixture
def alice(create_user):
    return create_user("Alice", "alice@example.com")


@pytest.fixture
def bob(create_user):
    return create_user("Bob", "bob@example.com")


def create_meeting(client, headers, attendee_ids=()):
    response = client.post(
        "/meetings/",
        json={"title": "Planning", "scheduled_time": "2024-01-15T10:00:00", "attendee_ids": list(attendee_ids)},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def alice_meeting(client, alice):
    _, headers = alice
    meeting = create_meeting(client, headers)
    note = client.post("/notes/", json={"content": "n", "meeting_id": meeting["id"]}, headers=headers).json()
    task = client.post("/tasks/", json={"title": "t", "due_meeting_id": meeting["id"]}, headers=headers).json()
    return meeting, note, task


def test_outsider_cannot_see_meeting_or_its_notes_and_tasks(client, alice_meeting, bob):
    meeting, note, task = alice_meeting
    _, headers = bob

    assert client.get("/meetings/", headers=headers).json() == []
    assert client.get("/notes/", headers=headers).json() == []
    assert client.get("/tasks/", headers=headers).json() == []
    assert client.get(f"/meetings/{meeting['id']}", headers=headers).status_code == 404
    assert client.get(f"/notes/{note['id']}", headers=headers).status_code == 404
    assert client.get(f"/tasks/{task['id']}", headers=headers).status_code == 404


def test_outsider_cannot_modify_meeting_or_its_tasks(client, alice_meeting, bob):
    meeting, _, task = alice_meeting
    _, headers = bob

    assert client.put(f"/meetings/{meeting['id']}", json={"title": "x"}, headers=headers).status_code == 404
    assert client.delete(f"/meetings/{meeting['id']}", headers=headers).status_code == 404
    assert client.put(f"/tasks/{task['id']}", json={"status": "completed"}, headers=headers).status_code == 404
    assert client.delete(f"/tasks/{task['id']}", headers=headers).status_code == 404


def test_outsider_cannot_add_notes_or_tasks_to_meeting(client, alice_meeting, bob):
    meeting, _, _ = alice_meeting
    _, headers = bob

    note = client.post("/notes/", json={"content": "x", "meeting_id": meeting["id"]}, headers=headers)
    task = client.post("/tasks/", json={"title": "x", "due_meeting_id": meeting["id"]}, headers=headers)

    assert note.status_code == 404
    assert task.status_code == 404


def test_cannot_move_task_to_inaccessible_meeting(client, alice, bob):
    _, alice_headers = alice
    _, bob_headers = bob
    alice_meeting = create_meeting(client, alice_headers)
    bob_meeting = create_meeting(client, bob_headers)
    task = client.post(
        "/tasks/", json={"title": "t", "due_meeting_id": bob_meeting["id"]}, headers=bob_headers
    ).json()

    response = client.put(
        f"/tasks/{task['id']}", json={"due_meeting_id": alice_meeting["id"]}, headers=bob_headers
    )

    assert response.status_code == 404


def test_attendee_can_see_and_update_meeting(client, alice, bob):
    _, alice_headers = alice
    bob_user, bob_headers = bob
    meeting = create_meeting(client, alice_headers, attendee_ids=[bob_user["id"]])
    client.post("/notes/", json={"content": "n", "meeting_id": meeting["id"]}, headers=alice_headers)

    assert [m["id"] for m in client.get("/meetings/", headers=bob_headers).json()] == [meeting["id"]]
    assert len(client.get("/notes/", headers=bob_headers).json()) == 1
    response = client.put(f"/meetings/{meeting['id']}", json={"title": "Renamed"}, headers=bob_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Renamed"


def test_only_owner_can_delete_meeting(client, alice, bob):
    _, alice_headers = alice
    bob_user, bob_headers = bob
    meeting = create_meeting(client, alice_headers, attendee_ids=[bob_user["id"]])

    assert client.delete(f"/meetings/{meeting['id']}", headers=bob_headers).status_code == 403
    assert client.delete(f"/meetings/{meeting['id']}", headers=alice_headers).status_code == 204


def test_users_only_see_themselves_and_meeting_peers(client, alice, bob, create_user):
    alice_user, alice_headers = alice
    bob_user, bob_headers = bob
    carol_user, _ = create_user("Carol", "carol@example.com")

    assert client.get("/users/", headers=bob_headers).json() == [bob_user]
    assert client.get(f"/users/{alice_user['id']}", headers=bob_headers).status_code == 404

    create_meeting(client, alice_headers, attendee_ids=[bob_user["id"]])

    assert client.get("/users/", headers=bob_headers).json() == [alice_user, bob_user]
    assert client.get(f"/users/{alice_user['id']}", headers=bob_headers).json() == alice_user
    assert client.get(f"/users/{carol_user['id']}", headers=bob_headers).status_code == 404
