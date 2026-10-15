from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base
from settings import settings

def create_db_engine(backend: str) -> Engine:
    """
    Create the engine for a storage backend (see Settings.mesh_backend).
    """
    if backend == "sqlite":
        return create_engine(settings.sqlite_database_url, connect_args={"check_same_thread": False})
    if backend == "memory":
        # A single shared connection, so every session sees the same in-memory database
        return create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
    raise ValueError(f"Unknown backend {backend!r}")


# Create engine
engine = create_db_engine(settings.mesh_backend)

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
