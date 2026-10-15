from sqlalchemy.orm import sessionmaker

import models
from database import create_db_engine
from models import Base
from settings import settings


def test_sqlite_backend_uses_configured_file():
    engine = create_db_engine("sqlite")

    assert str(engine.url) == settings.sqlite_database_url
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
