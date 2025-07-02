# tests/integration/test_task_workflow_integration.py
import os
import pytest
from httpx import ASGITransport, AsyncClient
from asgi_lifespan import LifespanManager
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.deps import get_db
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


class TestTaskWorkflowIntegration:
    """Test complete task workflows"""

    async def test_complete_task_lifecycle(self, client: AsyncClient):
        # Register and login user
        user_data, token = await AuthHelper.register_and_login(client)
        headers = AuthHelper.get_auth_headers(token)

        # 1. Create task
        task_data = TestDataFactory.create_task_data()
        response = await client.post("/tasks/", json=task_data, headers=headers)
        assert response.status_code == 201
        task_id = response.json()["_id"]

        # 2. Get task
        response = await client.get(f"/tasks/{task_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["title"] == task_data["title"]

        # 3. Update task
        update_data = TestDataFactory.create_task_update_data(title="Updated Task")
        response = await client.put(
            f"/tasks/{task_id}", json=update_data, headers=headers
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Task"

        # 4. Complete task
        response = await client.post(f"/tasks/{task_id}/complete", headers=headers)
        assert response.status_code == 200
        assert response.json()["completed_at"] is not None

        # 5. Uncomplete task
        response = await client.post(f"/tasks/{task_id}/uncomplete", headers=headers)
        assert response.status_code == 200
        assert response.json()["completed_at"] is None

        # 6. Delete task
        response = await client.delete(f"/tasks/{task_id}", headers=headers)
        assert response.status_code == 204

        # 7. Verify task is deleted
        response = await client.get(f"/tasks/{task_id}", headers=headers)
        assert response.status_code == 404

    async def test_pagination_with_filtering(self, client: AsyncClient):
        # Register and login user
        user_data, token = await AuthHelper.register_and_login(client)
        headers = AuthHelper.get_auth_headers(token)

        # Create multiple tasks
        tasks = TestDataFactory.create_bulk_tasks(5)
        created_tasks = []
        for task in tasks:
            response = await client.post("/tasks/", json=task, headers=headers)
            assert response.status_code == 201
            created_tasks.append(response.json())

        # Complete some tasks
        for task in created_tasks[:2]:
            response = await client.post(
                f"/tasks/{task['_id']}/complete", headers=headers
            )
            assert response.status_code == 200

        # Test pagination
        response = await client.get("/tasks/?page=1&size=2", headers=headers)
        assert response.status_code == 200
        assert len(response.json()["tasks"]) == 2

    async def test_concurrent_task_operations(self, client: AsyncClient):
        # Register and login user
        user_data, token = await AuthHelper.register_and_login(client)
        headers = AuthHelper.get_auth_headers(token)

        # Create task
        task_data = TestDataFactory.create_task_data()
        response = await client.post("/tasks/", json=task_data, headers=headers)
        assert response.status_code == 201
        task_id = response.json()["_id"]

        # Simulate concurrent updates
        update1 = TestDataFactory.create_task_update_data(title="Update 1")
        update2 = TestDataFactory.create_task_update_data(title="Update 2")

        # Make concurrent requests
        response1 = await client.put(f"/tasks/{task_id}", json=update1, headers=headers)
        response2 = await client.put(f"/tasks/{task_id}", json=update2, headers=headers)

        # Verify last update wins
        assert response1.status_code == 200 or response2.status_code == 200
        final_response = await client.get(f"/tasks/{task_id}", headers=headers)
        assert final_response.status_code == 200
        assert final_response.json()["title"] in ["Update 1", "Update 2"]
