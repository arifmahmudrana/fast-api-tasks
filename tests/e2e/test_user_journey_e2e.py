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


class TestUserJourneyE2E:
    """Test complete user journeys"""

    async def test_new_user_complete_journey(self, client: AsyncClient):
        """Test complete journey for a new user"""
        # 1. Register new user
        user_data = AuthHelper.create_user_data()
        register_response = await client.post("/users/register", json=user_data)
        assert register_response.status_code in (
            200,
            400,
        ), f"Registration failed: {register_response.text}"

        # 2. Login and get token
        token_response = await client.post(
            "/users/token",
            data={"username": user_data["email"], "password": user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert token_response.status_code == 200, f"Login failed: {token_response.text}"
        token = token_response.json()["access_token"]
        headers = AuthHelper.get_auth_headers(token)

        # 3. Create multiple tasks
        task_ids = []
        for i in range(3):
            task_data = TestDataFactory.create_task_data(f"Journey Task {i+1}")
            response = await client.post("/tasks/", json=task_data, headers=headers)
            assert response.status_code == 201
            task_ids.append(response.json()["_id"])

        # 4. Update first task
        update_data = TestDataFactory.create_task_update_data(
            title="Updated Journey Task 1"
        )
        response = await client.put(
            f"/tasks/{task_ids[0]}", json=update_data, headers=headers
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Journey Task 1"

        # 5. Complete second task
        response = await client.post(f"/tasks/{task_ids[1]}/complete", headers=headers)
        assert response.status_code == 200
        assert response.json()["completed_at"] is not None

        # 6. Delete third task
        response = await client.delete(f"/tasks/{task_ids[2]}", headers=headers)
        assert response.status_code == 204

        # 7. Verify final state
        response = await client.get("/tasks/", headers=headers)
        assert response.status_code == 200
        tasks = response.json()["tasks"]
        assert len(tasks) == 2  # One updated, one completed

        # Verify specific states
        updated_task = next(t for t in tasks if t["_id"] == task_ids[0])
        completed_task = next(t for t in tasks if t["_id"] == task_ids[1])

        assert updated_task["title"] == "Updated Journey Task 1"
        assert completed_task["completed_at"] is not None

    async def test_returning_user_journey(self, client: AsyncClient):
        """Test journey for a returning user"""
        # 1. Setup: Create user with existing tasks
        user_data, token = await AuthHelper.register_and_login(client)
        headers = AuthHelper.get_auth_headers(token)

        # Create initial tasks
        initial_tasks = TestDataFactory.create_bulk_tasks(3, "Initial Task")
        for task in initial_tasks:
            response = await client.post("/tasks/", json=task, headers=headers)
            assert response.status_code == 201

        # 2. Simulate returning user (new session)
        token_response = await client.post(
            "/users/token",
            data={"username": user_data["email"], "password": user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        headers = AuthHelper.get_auth_headers(token)

        # 3. List existing tasks
        response = await client.get("/tasks/", headers=headers)
        assert response.status_code == 200
        tasks = response.json()["tasks"]
        assert len(tasks) == 3

        # 4. Continue task operations
        # Complete all tasks
        for task in tasks:
            response = await client.post(
                f"/tasks/{task['_id']}/complete", headers=headers
            )
            assert response.status_code == 200

        # Verify all tasks are completed
        response = await client.get("/tasks/", headers=headers)
        assert response.status_code == 200
        tasks = response.json()["tasks"]
        assert all(task["completed_at"] is not None for task in tasks)

    async def test_multi_session_consistency(self, client: AsyncClient):
        """Test user working across multiple sessions"""
        # 1. Session 1: Register and create tasks
        user_data, token1 = await AuthHelper.register_and_login(client)
        headers1 = AuthHelper.get_auth_headers(token1)

        # Create tasks in first session
        task_data = TestDataFactory.create_task_data("Session 1 Task")
        response = await client.post("/tasks/", json=task_data, headers=headers1)
        assert response.status_code == 201
        task_id = response.json()["_id"]

        # 2. Session 2: Login and modify tasks
        token_response = await client.post(
            "/users/token",
            data={"username": user_data["email"], "password": user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert token_response.status_code == 200
        token2 = token_response.json()["access_token"]
        headers2 = AuthHelper.get_auth_headers(token2)

        # Modify task in second session
        update_data = TestDataFactory.create_task_update_data(title="Session 2 Update")
        response = await client.put(
            f"/tasks/{task_id}", json=update_data, headers=headers2
        )
        assert response.status_code == 200

        # 3. Session 3: Login and complete tasks
        token_response = await client.post(
            "/users/token",
            data={"username": user_data["email"], "password": user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert token_response.status_code == 200
        token3 = token_response.json()["access_token"]
        headers3 = AuthHelper.get_auth_headers(token3)

        # Complete task in third session
        response = await client.post(f"/tasks/{task_id}/complete", headers=headers3)
        assert response.status_code == 200

        # Verify final state in all sessions
        for headers in [headers1, headers2, headers3]:
            response = await client.get(f"/tasks/{task_id}", headers=headers)
            assert response.status_code == 200
            task = response.json()
            assert task["title"] == "Session 2 Update"
            assert task["completed_at"] is not None
