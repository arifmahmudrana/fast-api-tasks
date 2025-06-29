# tests/unit/test_main_unit.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import app, lifespan
from unittest.mock import AsyncMock


@pytest.fixture
def mock_mongo(mocker):
    """Fixture to mock all MongoDB operations"""
    mocks = {
        'connect': mocker.patch('app.mongo.connect_to_mongo', new_callable=AsyncMock),
        'disconnect': mocker.patch('app.mongo.disconnect_from_mongo', new_callable=AsyncMock),
        'ensure_indexes': mocker.patch('app.mongo.ensure_indexes', new_callable=AsyncMock)
    }
    return mocks


@pytest.fixture
def client():
    """Test client for FastAPI"""
    return TestClient(app)


@pytest.mark.asyncio
async def test_lifespan_success(mock_mongo):
    # Test the lifespan context manager
    mock_mongo['connect'].return_value = None
    mock_mongo['ensure_indexes'].return_value = None
    mock_mongo['disconnect'].return_value = None

    # Using the lifespan directly
    async with lifespan(app):
        pass

    # Assertions
    mock_mongo['connect'].assert_awaited_once()
    mock_mongo['ensure_indexes'].assert_awaited_once()
    mock_mongo['disconnect'].assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_connection_error(mock_mongo):
    # Test connection failure scenario
    mock_mongo['connect'].side_effect = Exception("Connection failed")

    with pytest.raises(Exception, match="Connection failed"):
        async with lifespan(app):
            pass

    mock_mongo['connect'].assert_awaited_once()
    mock_mongo['ensure_indexes'].assert_not_awaited()
    mock_mongo['disconnect'].assert_not_awaited()


def test_app_initialization(client, mock_mongo):
    # Test FastAPI app initialization
    assert isinstance(app, FastAPI)
    assert app.title == "FastAPI"
    assert len(app.routes) > 0  # Should have routes from included routers


def test_router_inclusion():
    # Verify routers are properly included
    routes = {route.path for route in app.routes}
    assert "/users" in str(routes)
    assert "/tasks" in str(routes)


@pytest.mark.asyncio
async def test_lifespan_in_actual_app(client, mock_mongo):
    # Integration-style test with TestClient
    mock_mongo['connect'].return_value = None
    mock_mongo['ensure_indexes'].return_value = None

    # This will trigger the lifespan
    with client:
        response = client.get("/")
        assert response.status_code == 404  # No root route

    mock_mongo['connect'].assert_awaited_once()
    mock_mongo['disconnect'].assert_awaited_once()
