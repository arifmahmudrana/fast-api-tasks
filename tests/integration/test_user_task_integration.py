# tests/integration/test_user_task_integration.py
import os
from asgi_lifespan import LifespanManager
import pytest
from httpx import ASGITransport, AsyncClient
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.deps import get_db
from app.main import app
from tests.helpers.auth_helpers import AuthHelper
from tests.helpers.data_factories import TestDataFactory

# --- Database setup ---
SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pytestmark = pytest.mark.asyncio


# --- Fixtures ---
@pytest_asyncio.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with LifespanManager(app):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()


class TestUserTaskIntegration:
    """Test user authentication with task operations"""

    async def test_authenticated_user_can_create_task(self, client: AsyncClient):
        # Register and login user
        user_data, token = await AuthHelper.register_and_login(client)
        headers = AuthHelper.get_auth_headers(token)

        # Create task
        task_data = TestDataFactory.create_task_data()
        response = await client.post("/tasks/", json=task_data, headers=headers)
        assert response.status_code == 201
        created_task = response.json()
        assert created_task["title"] == task_data["title"]
        assert created_task["description"] == task_data["description"]

    async def test_user_can_only_access_own_tasks(self, client: AsyncClient):
        # Create two users
        user1_data, user1_token = await AuthHelper.register_and_login(client)
        user2_data, user2_token = await AuthHelper.register_and_login(client)

        # User 1 creates a task
        task_data = TestDataFactory.create_task_data("User 1 Task")
        response = await client.post(
            "/tasks/", json=task_data, headers=AuthHelper.get_auth_headers(user1_token)
        )
        assert response.status_code == 201
        task_id = response.json()["_id"]

        # User 2 tries to access User 1's task
        response = await client.get(
            f"/tasks/{task_id}", headers=AuthHelper.get_auth_headers(user2_token)
        )
        assert response.status_code == 404  # Should not find task

    async def test_token_expiry_blocks_task_access(self, client: AsyncClient):
        # Register and login user
        user_data, token = await AuthHelper.register_and_login(client)
        headers = AuthHelper.get_auth_headers(token)

        # Create task
        task_data = TestDataFactory.create_task_data()
        response = await client.post("/tasks/", json=task_data, headers=headers)
        assert response.status_code == 201
        task_id = response.json()["_id"]

        # Try to access with expired token (simulated by invalid token)
        headers = AuthHelper.get_auth_headers("invalid_token")
        response = await client.get(f"/tasks/{task_id}", headers=headers)
        assert response.status_code == 401  # Unauthorized
