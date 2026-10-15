import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import get_db
from main import app
import models
from mesh import build_local_mesh, default_cache
from middleware import USER_ID_HEADER
from models import Base


@pytest.fixture(autouse=True)
def clear_cache():
    """
    Every test gets a fresh database, so cached results from earlier tests
    (keyed by the same ids) must not leak into it.
    """
    default_cache.clear()
    yield
    default_cache.clear()


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    yield sessionmaker(autocommit=False, autoflush=False, bind=engine)
    engine.dispose()


@pytest.fixture
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def client(session_factory):
    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def create_user(client):
    """
    Factory creating a user through the API; returns (user, auth headers).
    """

    def create(name, email):
        response = client.post("/users/", json={"name": name, "email": email})
        assert response.status_code == 201
        user = response.json()
        return user, {USER_ID_HEADER: str(user["id"])}

    return create


@pytest.fixture
def user_and_headers(create_user):
    return create_user("Ada", "ada@example.com")


@pytest.fixture
def user(user_and_headers):
    return user_and_headers[0]


@pytest.fixture
def auth_headers(user_and_headers):
    return user_and_headers[1]


@pytest.fixture
def db_user(db):
    user = models.User(name="Ada", email="ada@example.com")
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def mesh(db, db_user):
    return build_local_mesh(db, user_id=db_user.id)
