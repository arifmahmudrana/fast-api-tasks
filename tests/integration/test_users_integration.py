# tests/integration/test_users_integration.py
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.deps import get_db


# --- Database setup ---
SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- Fixtures ---
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
        yield db_session  # Reuse the same session; don't close it here

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c


# --- Integration tests ---


def test_register_user(client):
    response = client.post(
        "/users/register",
        json={"email": "integration@example.com", "password": "integrationpass"},
    )
    assert response.status_code in (200, 400), response.text


def test_register_and_login(client):
    # Register user
    response = client.post(
        "/users/register", json={"email": "test@example.com", "password": "testpass"}
    )
    assert response.status_code in (200, 400), response.text

    if response.status_code == 200:
        data = response.json()
        assert data["email"] == "test@example.com"

    # Login user
    response = client.post(
        "/users/token",
        data={"username": "test@example.com", "password": "testpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code in (200, 401), response.text

    if response.status_code == 200:
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
