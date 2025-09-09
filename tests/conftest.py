import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime as dt

from app.main import app
from app.database import get_db
from app.models import Base, User, Event
from app.schemas import EventCreate
from app.services import create_event as create_event_service

SQLALCHEMY_DATABASE_URL = "sqlite:///file:memdb1?mode=memory&cache=shared&uri=true"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def setup_test_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(setup_test_database):
    d = TestingSessionLocal()
    try:
        d.add(User(id=1, email="test@example.com", username="testuser", role="user"))
        d.add(User(id=2, email="admin@example.com", username="adminuser", role="admin"))
        d.commit()
        yield d
    finally:
        d.close()


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
