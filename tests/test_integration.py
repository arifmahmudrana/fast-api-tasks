import tests.setuptest  # noqa: F401
from fastapi.testclient import TestClient
from app.main import app
from app.deps import get_db
from app.database import Base
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, text
import pytest
import os
SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]


engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Do not close db_session here
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


# Example integration test
def test_register_user(client):
    response = client.post(
        "/users/register", json={"email": "integration@example.com", "password": "integrationpass"})
    assert response.status_code in (200, 400)
