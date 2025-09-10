import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from alembic.config import Config
from alembic import command

from app.main import app
from app.database import get_db
from app.models import User

SQLALCHEMY_DATABASE_URL = "sqlite:///file:memdb1?mode=memory&cache=shared&uri=true"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def setup_test_database():
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

    with engine.connect() as connection:
        alembic_cfg.attributes["connection"] = connection

        command.upgrade(alembic_cfg, "head")

        db_session = TestingSessionLocal(bind=connection)
        try:
            db_session.add(User(id=1, email="test@example.com", username="testuser", role="user"))
            db_session.add(User(id=2, email="admin@example.com", username="adminuser", role="admin"))
            db_session.commit()
        finally:
            db_session.close()
        
        yield connection

        command.downgrade(alembic_cfg, "base")

@pytest.fixture(scope="function")
def db(setup_test_database) -> Session:
    db_session = TestingSessionLocal(bind=setup_test_database)
    try:
        yield db_session
    finally:
        db_session.close()


@pytest.fixture(scope="function")
def client(db: Session):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
