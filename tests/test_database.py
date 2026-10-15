import pytest
from sqlalchemy.orm import sessionmaker

import models
from database import create_db_engine, get_backend
from models import Base


def test_backend_defaults_to_sqlite(monkeypatch):
    monkeypatch.delenv("MESH_BACKEND", raising=False)

    assert get_backend() == "sqlite"


@pytest.mark.parametrize("backend", ["sqlite", "memory"])
def test_backend_is_read_from_environment(monkeypatch, backend):
    monkeypatch.setenv("MESH_BACKEND", backend)

    assert get_backend() == backend


def test_unknown_backend_is_rejected(monkeypatch):
    monkeypatch.setenv("MESH_BACKEND", "postgres")

    with pytest.raises(ValueError, match="postgres"):
        get_backend()


def test_sqlite_backend_uses_meetings_db_file():
    engine = create_db_engine("sqlite")

    assert engine.url.database == "./meetings.db"
    engine.dispose()


def test_memory_backend_shares_data_across_sessions():
    engine = create_db_engine("memory")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        session.add(models.User(name="Ada", email="ada@example.com"))
        session.commit()
    with Session() as session:
        assert [user.name for user in session.query(models.User)] == ["Ada"]

    engine.dispose()
