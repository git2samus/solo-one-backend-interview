import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base

# Database configuration
SQLITE_DATABASE_URL = "sqlite:///./meetings.db"

# MESH_BACKEND selects where the services store data:
#   sqlite - the meetings.db file (default)
#   memory - an in-memory SQLite database, wiped when the process exits
BACKENDS = ("sqlite", "memory")


def get_backend() -> str:
    """
    Read the storage backend from the MESH_BACKEND environment variable.
    """
    backend = os.environ.get("MESH_BACKEND", "sqlite")
    if backend not in BACKENDS:
        raise ValueError(f"Unknown MESH_BACKEND {backend!r}; expected one of {', '.join(BACKENDS)}")
    return backend


def create_db_engine(backend: str) -> Engine:
    """
    Create the engine for a storage backend.
    """
    if backend == "sqlite":
        return create_engine(SQLITE_DATABASE_URL, connect_args={"check_same_thread": False})
    if backend == "memory":
        # A single shared connection, so every session sees the same in-memory database
        return create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
    raise ValueError(f"Unknown backend {backend!r}; expected one of {', '.join(BACKENDS)}")


# Create engine
engine = create_db_engine(get_backend())

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """
    Create all tables in the database.
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
