import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from middleware import USER_ID_HEADER, UserIdMiddleware, get_current_user_id

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
    assert response.json() == {"detail": f"Missing {USER_ID_HEADER} header"}


@pytest.mark.parametrize("value", ["abc", "1.5", ""])
def test_non_integer_header_returns_400(client, value):
    response = client.get("/users/", headers={USER_ID_HEADER: value})

    assert response.status_code == 400
    assert response.json() == {"detail": f"{USER_ID_HEADER} header must be an integer"}


@pytest.mark.parametrize("path", ["/users/", "/meetings/", "/notes/", "/tasks/"])
def test_valid_header_is_accepted(client, path):
    response = client.get(path, headers={USER_ID_HEADER: "7"})

    assert response.status_code == 200


def test_user_id_is_passed_to_view():
    app = FastAPI()
    app.add_middleware(UserIdMiddleware)

    @app.get("/whoami")
    async def whoami(current_user_id: int = Depends(get_current_user_id)):
        return {"user_id": current_user_id}

    response = TestClient(app).get("/whoami", headers={USER_ID_HEADER: "42"})

    assert response.status_code == 200
    assert response.json() == {"user_id": 42}
