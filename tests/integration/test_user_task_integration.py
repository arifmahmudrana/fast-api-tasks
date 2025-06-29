import pytest
from httpx import AsyncClient

from tests.helpers.auth_helpers import AuthHelper
from tests.helpers.data_factories import TestDataFactory

pytestmark = pytest.mark.asyncio

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
            "/tasks/",
            json=task_data,
            headers=AuthHelper.get_auth_headers(user1_token)
        )
        assert response.status_code == 201
        task_id = response.json()["id"]
        
        # User 2 tries to access User 1's task
        response = await client.get(
            f"/tasks/{task_id}",
            headers=AuthHelper.get_auth_headers(user2_token)
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
        task_id = response.json()["id"]
        
        # Try to access with expired token (simulated by invalid token)
        headers = AuthHelper.get_auth_headers("invalid_token")
        response = await client.get(f"/tasks/{task_id}", headers=headers)
        assert response.status_code == 401  # Unauthorized 
