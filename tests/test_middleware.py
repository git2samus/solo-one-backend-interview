import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from middleware import UserIdMiddleware, get_current_user_id
from settings import settings

PROTECTED_ENDPOINTS = [
    ("get", "/users/"),
    ("get", "/users/1"),
    ("get", "/meetings/"),
    ("get", "/meetings/1"),
    ("delete", "/meetings/1"),
    ("get", "/notes/"),
    ("get", "/notes/1"),
    ("get", "/tasks/"),
    ("get", "/tasks/1"),
    ("delete", "/tasks/1"),
]


@pytest.mark.parametrize("path", ["/", "/docs", "/openapi.json"])
def test_public_endpoints_do_not_require_header(client, path):
    assert client.get(path).status_code == 200


@pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
def test_missing_header_returns_401(client, method, path):
    response = client.request(method, path)

    assert response.status_code == 401
    assert response.json() == {"detail": f"Missing {settings.user_id_header} header"}


@pytest.mark.parametrize("value", ["abc", "1.5", ""])
def test_non_integer_header_returns_400(client, value):
    response = client.get("/users/", headers={settings.user_id_header: value})

    assert response.status_code == 400
    assert response.json() == {"detail": f"{settings.user_id_header} header must be an integer"}


@pytest.mark.parametrize("path", ["/users/", "/meetings/", "/notes/", "/tasks/"])
def test_valid_header_is_accepted(client, auth_headers, path):
    assert client.get(path, headers=auth_headers).status_code == 200


def test_unknown_user_returns_401(client):
    response = client.get("/meetings/", headers={settings.user_id_header: "999"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Unknown user 999"}


def test_create_user_does_not_require_header(client):
    response = client.post("/users/", json={"name": "Ada", "email": "ada@example.com"})

    assert response.status_code == 201


def test_user_id_is_passed_to_view():
    app = FastAPI()
    app.add_middleware(UserIdMiddleware)

    @app.get("/whoami")
    async def whoami(current_user_id: int = Depends(get_current_user_id)):
        return {"user_id": current_user_id}

    response = TestClient(app).get("/whoami", headers={settings.user_id_header: "42"})

    assert response.status_code == 200
    assert response.json() == {"user_id": 42}


def test_openapi_declares_user_id_header_for_swagger(client):
    schema = client.get("/openapi.json").json()

    schemes = schema["components"]["securitySchemes"]
    assert schemes == {
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": settings.user_id_header,
            "description": schemes["APIKeyHeader"]["description"],
        }
    }
    assert schema["paths"]["/meetings/"]["get"]["security"] == [{"APIKeyHeader": []}]
    assert "security" not in schema["paths"]["/users/"]["post"]
