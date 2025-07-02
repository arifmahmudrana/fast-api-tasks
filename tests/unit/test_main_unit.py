# tests/unit/test_main_unit.py
from importlib import reload
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def mock_mongo(mocker):
    """Fixture to mock all MongoDB operations with proper patching"""
    # Patch before importing the app
    mocks = {
        "connect": mocker.patch("app.mongo.connect_to_mongo", new_callable=AsyncMock),
        "disconnect": mocker.patch(
            "app.mongo.disconnect_from_mongo", new_callable=AsyncMock
        ),
        "ensure_indexes": mocker.patch(
            "app.mongo.ensure_indexes", new_callable=AsyncMock
        ),
    }
    return mocks


@pytest.fixture
def app_with_mocks(mock_mongo):
    """Fixture that provides the app with mocks already in place"""
    # Need to reload the module to apply mocks
    from app import main

    reload(main)
    return main.app


@pytest.fixture
def client(app_with_mocks):
    """Test client using the mocked app"""
    return TestClient(app_with_mocks)


@pytest.mark.asyncio
async def test_lifespan_success(app_with_mocks, mock_mongo):
    # Configure mocks
    mock_mongo["connect"].return_value = None
    mock_mongo["ensure_indexes"].return_value = None
    mock_mongo["disconnect"].return_value = None

    # Get the lifespan function from the reloaded module
    from app.main import lifespan

    async with lifespan(app_with_mocks):
        pass

    # Assertions
    mock_mongo["connect"].assert_awaited_once()
    mock_mongo["ensure_indexes"].assert_awaited_once()
    mock_mongo["disconnect"].assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_connection_error(app_with_mocks, mock_mongo):
    # Configure mocks
    mock_mongo["connect"].side_effect = Exception("Connection failed")
    mock_mongo["ensure_indexes"].assert_not_awaited()
    mock_mongo["disconnect"].assert_not_awaited()

    from app.main import lifespan

    with pytest.raises(Exception, match="Connection failed"):
        async with lifespan(app_with_mocks):
            pass


def test_app_initialization(app_with_mocks):
    assert isinstance(app_with_mocks, FastAPI)
    assert app_with_mocks.title == "FastAPI"
    assert len(app_with_mocks.routes) > 0


def test_router_inclusion(app_with_mocks):
    routes = {route.path for route in app_with_mocks.routes}
    assert "/users" in str(routes)
    assert "/tasks" in str(routes)


@pytest.mark.asyncio
async def test_lifespan_in_actual_app(client, mock_mongo):
    # Configure mocks
    mock_mongo["connect"].return_value = None
    mock_mongo["ensure_indexes"].return_value = None

    # This will trigger the lifespan
    with client:
        response = client.get("/")
        assert response.status_code == 404

    mock_mongo["connect"].assert_awaited_once()
    mock_mongo["disconnect"].assert_awaited_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
