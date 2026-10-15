from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration.

    Every field can be overridden by an environment variable of the same name
    in upper case (e.g. MESH_BACKEND=memory), or by a .env file in the working
    directory.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # API metadata
    app_title: str = "Meeting Notes API"
    app_description: str = "API for managing meetings, notes, and tasks"
    app_version: str = "1.0.0"

    # Where the services store data:
    #   sqlite - the file at sqlite_database_url
    #   memory - an in-memory SQLite database, wiped when the process exits
    mesh_backend: Literal["sqlite", "memory"] = "sqlite"
    sqlite_database_url: str = "sqlite:///./meetings.db"

    # Request header carrying the id of the user making the request
    user_id_header: str = "X-User-ID"


settings = Settings()
