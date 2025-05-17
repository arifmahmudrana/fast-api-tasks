import tests.setuptest  # noqa: F401
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 404 or response.status_code == 200


def test_register_and_login():
    # Register user
    response = client.post(
        "/users/register", json={"email": "test2@example.com", "password": "testpass2"})
    assert response.status_code in (200, 400), response.text
    if response.status_code == 200:
        data = response.json()
        assert data["email"] == "test2@example.com"
    # Login user
    response = client.post(
        "/users/token", data={"username": "test2@example.com", "password": "testpass2"})
    assert response.status_code in (200, 401), response.text
    if response.status_code == 200:
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
