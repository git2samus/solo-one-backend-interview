# backend-inteview

A FastAPI application for managing meetings, notes, and tasks.

## Your task

Implement all endpoints through a service layer and write it to the database, then assert that you can read it again.

To do this:

- Add authentication. Do this however you would like (external libraries are allowed). Keep it as simple as possible though.
- Create a service per resource that all implement a base service class.
- Put all of the services into a service mesh. Call's between each service should route through the mesh.
- The service mesh is user specific, and should should support caching.
- The mesh should support local development, and cloud development, and should be composable in order to accomplish this. Ie, local development is in memory, but in production the service mesh might allow gRPC connections between services seamlessly in production. Note you do not need to support gRPC for this task - but design this in such a way that the communication mode between services is easily interchangeable.
- Create a decorator that can be placed on each service. This decorator allows us to call service_mesh.get_tools(), which can be passed onwards to an LLM.
- The service mesh (and the services within in) should only be able to access resources that only the user making the request.

## Features

- **Users**: Create users and see the people you share meetings with
- **Meetings**: Schedule meetings with attendees
- **Notes**: Add notes to meetings
- **Tasks**: Create tasks due at specific meetings

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. Database tables are created on startup.

## Configuration

Settings live in `settings.py`. Each one can be overridden with an environment variable of the same name in upper case, or with a `.env` file in the project root (environment variables take precedence):

| Variable | Default | Description |
|---|---|---|
| `MESH_BACKEND` | `sqlite` | Where data is stored: `sqlite` (the file at `SQLITE_DATABASE_URL`) or `memory` (an in-memory database, wiped on restart) |
| `SQLITE_DATABASE_URL` | `sqlite:///./meetings.db` | SQLite database used by the `sqlite` backend |
| `USER_ID_HEADER` | `X-User-ID` | Request header that identifies the user |
| `APP_TITLE`, `APP_DESCRIPTION`, `APP_VERSION` | | Metadata shown in the API docs |

For example, to run with a throwaway in-memory database:
```bash
MESH_BACKEND=memory uvicorn main:app --reload
```

Invalid values (e.g. `MESH_BACKEND=postgres`) stop the application at startup.

There are no migrations: tables are only created if missing, so after a change to `models.py` delete `meetings.db` to recreate it.

## Running Tests

Tests live in `tests/` and use pytest with FastAPI's `TestClient`, so no running server is needed. Each test runs against its own in-memory database, so tests never touch `meetings.db`. After installing dependencies, run from the project root:
```bash
pytest
```

To run a single file or test:
```bash
pytest tests/test_middleware.py
pytest tests/test_middleware.py::test_user_id_is_passed_to_view
```

## Authentication

Requests identify the user with the `X-User-ID` header, set to the ID of an existing user:

```bash
curl http://localhost:8000/meetings/ -H "X-User-ID: 1"
```

- Every endpoint requires the header except `POST /users/` (sign-up) and the docs.
- A missing header, or one naming a user that doesn't exist, returns `401`; a non-integer value returns `400`.
- The header is trusted as-is: there are no passwords or tokens, so this is only suitable for development.

## API Documentation

Once the server is running, you can access:
- Interactive API docs (Swagger UI): `http://localhost:8000/docs`
- Alternative API docs (ReDoc): `http://localhost:8000/redoc`
- OpenAPI schema: `http://localhost:8000/openapi.json`

To call protected endpoints from Swagger UI, create a user with `POST /users/`, then click **Authorize**, enter the user's ID and confirm. Swagger UI then sends it as the `X-User-ID` header on every request.

## API Endpoints

Every endpoint only sees the data the requesting user has access to:

- **Meetings**: those you own (created) or attend.
- **Notes and tasks**: those on meetings you can access.
- **Users**: yourself and anyone you share a meeting with. Any existing user can be invited as an attendee.

Resources you can't access respond as if they don't exist (`404`).

### Users
- `POST /users/` - Create a new user (no `X-User-ID` header needed)
- `GET /users/` - List yourself and the users you share meetings with
- `GET /users/{user_id}` - Get a specific user

### Meetings
- `POST /meetings/` - Create a new meeting with attendees; you become its owner
- `GET /meetings/` - List the meetings you own or attend
- `GET /meetings/{meeting_id}` - Get a specific meeting with attendees, notes and tasks
- `PUT /meetings/{meeting_id}` - Update a meeting (only the fields sent change; `attendee_ids` replaces the full list)
- `DELETE /meetings/{meeting_id}` - Delete a meeting and its notes (owner only, and only once it has no tasks)

### Notes
- `POST /notes/` - Create a new note for a meeting
- `GET /notes/` - List notes (can filter by `meeting_id`)
- `GET /notes/{note_id}` - Get a specific note

### Tasks
- `POST /tasks/` - Create a new task due at a meeting
- `GET /tasks/` - List tasks (can filter by `meeting_id` or `status`)
- `GET /tasks/{task_id}` - Get a specific task
- `PUT /tasks/{task_id}` - Update a task (change status, reassign to a different meeting)
- `DELETE /tasks/{task_id}` - Delete a task

Task `status` is one of `pending` (default), `completed` or `cancelled`.

### Error responses

| Status | When |
|---|---|
| `400` | `X-User-ID` is not an integer |
| `401` | `X-User-ID` is missing or names a user that doesn't exist |
| `403` | Deleting a meeting you attend but don't own |
| `404` | The resource doesn't exist or you can't access it; also an unknown `attendee_ids` or meeting ID in the request |
| `409` | Creating a user with an email already in use; deleting a meeting that still has tasks |
| `422` | Invalid request body or query parameters (e.g. an unknown task `status`) |

## Example Usage

### Create users
No `X-User-ID` header is needed to sign up:
```bash
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Roe", "email": "jane@example.com"}'
```

### Create a meeting
As user 1, inviting user 2:
```bash
curl -X POST http://localhost:8000/meetings/ \
  -H "Content-Type: application/json" \
  -H "X-User-ID: 1" \
  -d '{
    "title": "Sprint Planning",
    "description": "Q1 Sprint Planning",
    "scheduled_time": "2024-01-15T10:00:00",
    "attendee_ids": [2]
  }'
```

### Create a task for a meeting
```bash
curl -X POST http://localhost:8000/tasks/ \
  -H "Content-Type: application/json" \
  -H "X-User-ID: 1" \
  -d '{
    "title": "Implement feature X",
    "description": "Complete implementation",
    "due_meeting_id": 1
  }'
```

### Add a note to a meeting
User 2 attends the meeting, so they can add notes too:
```bash
curl -X POST http://localhost:8000/notes/ \
  -H "Content-Type: application/json" \
  -H "X-User-ID: 2" \
  -d '{
    "content": "This is a meeting note",
    "meeting_id": 1
  }'
```

### Complete a task
```bash
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -H "X-User-ID: 1" \
  -d '{"status": "completed"}'
```

### Get a meeting with its notes and tasks
```bash
curl http://localhost:8000/meetings/1 -H "X-User-ID: 2"
```

## Using the services as LLM tools

The service mesh can describe its operations as tools for an LLM, and run the tool calls the model makes. Calls run as the mesh's user, so the same access rules apply:

```python
from database import SessionLocal
from mesh import build_local_mesh

with SessionLocal() as db:
    mesh = build_local_mesh(db, user_id=1)

    tools = mesh.get_tools()  # pass as `tools` to the Anthropic Messages API

    # For each tool_use block in the model's response:
    result = mesh.call_tool("meetings_list", {})
```

`get_tools()` returns definitions in the Anthropic API format (`name`, `description`, `input_schema`). `call_tool()` returns a JSON-compatible result, and raises if the input is invalid or the resource isn't accessible; send those errors back to the model as a `tool_result` with `is_error: true`.
