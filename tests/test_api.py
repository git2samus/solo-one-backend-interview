import pytest


@pytest.fixture
def meeting(client, auth_headers, user):
    response = client.post(
        "/meetings/",
        json={
            "title": "Sprint Planning",
            "description": "Q1",
            "scheduled_time": "2024-01-15T10:00:00",
            "attendee_ids": [user["id"]],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


def test_create_and_read_user(client, auth_headers, user):
    assert client.get(f"/users/{user['id']}", headers=auth_headers).json() == user
    assert client.get("/users/", headers=auth_headers).json() == [user]


def test_duplicate_user_email_returns_409(client, auth_headers, user):
    response = client.post(
        "/users/", json={"name": "Other", "email": user["email"]}, headers=auth_headers
    )

    assert response.status_code == 409


def test_create_and_read_meeting(client, auth_headers, user, meeting):
    assert meeting["attendees"] == [user]
    assert meeting["owner_id"] == user["id"]

    details = client.get(f"/meetings/{meeting['id']}", headers=auth_headers).json()

    assert details == {**meeting, "notes": [], "tasks": []}
    assert client.get("/meetings/", headers=auth_headers).json() == [meeting]


def test_create_meeting_with_unknown_attendee_returns_404(client, auth_headers):
    response = client.post(
        "/meetings/",
        json={"title": "x", "scheduled_time": "2024-01-15T10:00:00", "attendee_ids": [99]},
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_update_meeting(client, auth_headers, meeting):
    response = client.put(
        f"/meetings/{meeting['id']}",
        json={"title": "Retro", "attendee_ids": []},
        headers=auth_headers,
    )

    assert response.status_code == 200
    updated = client.get(f"/meetings/{meeting['id']}", headers=auth_headers).json()
    assert updated["title"] == "Retro"
    assert updated["description"] == "Q1"
    assert updated["attendees"] == []


def test_delete_meeting(client, auth_headers, meeting):
    assert client.delete(f"/meetings/{meeting['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/meetings/{meeting['id']}", headers=auth_headers).status_code == 404


def test_delete_meeting_with_tasks_returns_409(client, auth_headers, meeting):
    client.post(
        "/tasks/", json={"title": "t", "due_meeting_id": meeting["id"]}, headers=auth_headers
    )

    response = client.delete(f"/meetings/{meeting['id']}", headers=auth_headers)

    assert response.status_code == 409


def test_create_and_read_note(client, auth_headers, meeting):
    response = client.post(
        "/notes/", json={"content": "hello", "meeting_id": meeting["id"]}, headers=auth_headers
    )
    assert response.status_code == 201
    note = response.json()

    assert client.get(f"/notes/{note['id']}", headers=auth_headers).json() == note
    assert client.get(f"/notes/?meeting_id={meeting['id']}", headers=auth_headers).json() == [note]
    assert client.get("/notes/?meeting_id=999", headers=auth_headers).json() == []
    assert client.get(f"/meetings/{meeting['id']}", headers=auth_headers).json()["notes"] == [note]


def test_create_note_for_unknown_meeting_returns_404(client, auth_headers):
    response = client.post("/notes/", json={"content": "x", "meeting_id": 99}, headers=auth_headers)

    assert response.status_code == 404


def test_task_lifecycle(client, auth_headers, meeting):
    response = client.post(
        "/tasks/", json={"title": "Write docs", "due_meeting_id": meeting["id"]}, headers=auth_headers
    )
    assert response.status_code == 201
    task = response.json()
    assert task["status"] == "pending"
    assert client.get(f"/tasks/{task['id']}", headers=auth_headers).json() == task

    response = client.put(f"/tasks/{task['id']}", json={"status": "completed"}, headers=auth_headers)
    assert response.json()["status"] == "completed"
    assert client.get("/tasks/?status=completed", headers=auth_headers).json() == [response.json()]
    assert client.get("/tasks/?status=pending", headers=auth_headers).json() == []

    assert client.delete(f"/tasks/{task['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/tasks/{task['id']}", headers=auth_headers).status_code == 404


def test_reassign_task_to_unknown_meeting_returns_404(client, auth_headers, meeting):
    task = client.post(
        "/tasks/", json={"title": "t", "due_meeting_id": meeting["id"]}, headers=auth_headers
    ).json()

    response = client.put(f"/tasks/{task['id']}", json={"due_meeting_id": 99}, headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.parametrize("path", ["/users/999", "/meetings/999", "/notes/999", "/tasks/999"])
def test_unknown_resource_returns_404(client, auth_headers, path):
    assert client.get(path, headers=auth_headers).status_code == 404
