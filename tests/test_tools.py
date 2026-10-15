import json

import pytest
from pydantic import BaseModel, ValidationError

import models
from mesh import TOOLS, build_local_mesh
from services import NotFoundError
from tools import collect_tools, expose_tools


@pytest.fixture
def bob_mesh(db):
    bob = models.User(name="Bob", email="bob@example.com")
    db.add(bob)
    db.commit()
    return build_local_mesh(db, user_id=bob.id)


def create_meeting(mesh, **overrides):
    return mesh.call_tool(
        "meetings_create",
        {"title": "Standup", "scheduled_time": "2024-01-15T10:00:00", **overrides},
    )


def test_get_tools_lists_crud_methods_of_every_service(mesh):
    names = {tool["name"] for tool in mesh.get_tools()}

    assert names == {
        "users_create", "users_list", "users_get",
        "meetings_create", "meetings_list", "meetings_get", "meetings_update", "meetings_delete",
        "notes_create", "notes_list", "notes_get",
        "tasks_create", "tasks_list", "tasks_get", "tasks_update", "tasks_delete",
    }


def test_tool_definitions_have_llm_format(mesh):
    for tool in mesh.get_tools():
        assert set(tool) == {"name", "description", "input_schema"}
        assert tool["description"]
        assert tool["input_schema"]["type"] == "object"
        json.dumps(tool)


def test_model_parameters_are_flattened_into_the_input(mesh):
    tools = {tool["name"]: tool for tool in mesh.get_tools()}

    create = tools["meetings_create"]["input_schema"]
    assert set(create["properties"]) == {"title", "description", "scheduled_time", "attendee_ids"}
    assert set(create["required"]) == {"title", "scheduled_time"}

    update = tools["tasks_update"]["input_schema"]
    assert set(update["properties"]) == {"task_id", "title", "description", "status", "due_meeting_id"}
    assert update["required"] == ["task_id"]


def test_call_tool_round_trip_returns_json_compatible_results(mesh, db_user):
    meeting = create_meeting(mesh)

    fetched = mesh.call_tool("meetings_get", {"meeting_id": meeting["id"]})

    assert fetched["title"] == "Standup"
    assert fetched["owner_id"] == db_user.id
    assert fetched["scheduled_time"] == "2024-01-15T10:00:00"
    json.dumps(fetched)


def test_call_tool_update_only_changes_provided_fields(mesh):
    meeting = create_meeting(mesh, description="Daily")

    mesh.call_tool("meetings_update", {"meeting_id": meeting["id"], "title": "Retro"})

    fetched = mesh.call_tool("meetings_get", {"meeting_id": meeting["id"]})
    assert (fetched["title"], fetched["description"]) == ("Retro", "Daily")


def test_call_tool_is_scoped_to_the_mesh_user(mesh, bob_mesh):
    meeting = create_meeting(mesh)

    with pytest.raises(NotFoundError):
        bob_mesh.call_tool("meetings_get", {"meeting_id": meeting["id"]})
    assert bob_mesh.call_tool("meetings_list", {}) == []


def test_call_tool_validates_input(mesh):
    with pytest.raises(ValidationError):
        mesh.call_tool("meetings_create", {"title": "No time"})


def test_call_tool_rejects_unknown_tool(mesh):
    with pytest.raises(KeyError):
        mesh.call_tool("meetings_explode", {})


def test_internal_methods_are_not_exposed():
    assert "meetings_accessible_ids" not in TOOLS


class Payload(BaseModel):
    value: int


def test_methods_argument_overrides_defaults():
    @expose_tools(methods=["ping"])
    class Service:
        name = "things"

        def get(self, thing_id: int):
            """Get a thing."""

        def ping(self, payload: Payload):
            """Ping."""

    tools = collect_tools([Service])

    assert list(tools) == ["things_ping"]
    assert tools["things_ping"].arguments({"value": 3}) == {"payload": Payload(value=3)}


def test_exposed_method_requires_docstring():
    with pytest.raises(TypeError, match="docstring"):
        @expose_tools
        class Service:
            name = "things"

            def get(self, thing_id: int):
                pass


def test_clashing_input_fields_are_rejected():
    with pytest.raises(TypeError, match="value"):
        @expose_tools
        class Service:
            name = "things"

            def update(self, value: int, payload: Payload):
                """Update a thing."""


def test_undecorated_services_have_no_tools():
    class Service:
        name = "things"

        def get(self, thing_id: int):
            """Get a thing."""

    assert collect_tools([Service]) == {}


def test_task_status_values_are_listed_in_tool_schema(mesh):
    tools = {tool["name"]: tool for tool in mesh.get_tools()}
    status = tools["tasks_create"]["input_schema"]["properties"]["status"]

    assert status["enum"] == ["pending", "completed", "cancelled"]


def test_call_tool_rejects_unknown_task_status(mesh):
    meeting = create_meeting(mesh)

    with pytest.raises(ValidationError):
        mesh.call_tool("tasks_create", {"title": "t", "due_meeting_id": meeting["id"], "status": "done"})
