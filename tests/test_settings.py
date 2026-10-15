import pytest
from pydantic import ValidationError

from settings import Settings

ENV_VARS = (
    "APP_TITLE", "APP_DESCRIPTION", "APP_VERSION",
    "MESH_BACKEND", "SQLITE_DATABASE_URL", "USER_ID_HEADER",
)


@pytest.fixture
def clean_env(monkeypatch):
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def load():
    return Settings(_env_file=None)


def test_defaults(clean_env):
    settings = load()

    assert settings.mesh_backend == "sqlite"
    assert settings.sqlite_database_url == "sqlite:///./meetings.db"
    assert settings.user_id_header == "X-User-ID"
    assert settings.app_version == "1.0.0"


@pytest.mark.parametrize("backend", ["sqlite", "memory"])
def test_backend_is_read_from_environment(clean_env, backend):
    clean_env.setenv("MESH_BACKEND", backend)

    assert load().mesh_backend == backend


def test_unknown_backend_is_rejected(clean_env):
    clean_env.setenv("MESH_BACKEND", "postgres")

    with pytest.raises(ValidationError, match="mesh_backend"):
        load()


def test_other_fields_are_read_from_environment(clean_env):
    clean_env.setenv("SQLITE_DATABASE_URL", "sqlite:///./other.db")
    clean_env.setenv("USER_ID_HEADER", "X-Account")

    settings = load()

    assert settings.sqlite_database_url == "sqlite:///./other.db"
    assert settings.user_id_header == "X-Account"


def test_values_are_read_from_env_file(clean_env, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("MESH_BACKEND=memory\n")

    assert Settings(_env_file=env_file).mesh_backend == "memory"


def test_environment_overrides_env_file(clean_env, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("MESH_BACKEND=memory\n")
    clean_env.setenv("MESH_BACKEND", "sqlite")

    assert Settings(_env_file=env_file).mesh_backend == "sqlite"
