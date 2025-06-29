import pytest
from httpx import AsyncClient

from tests.helpers.auth_helpers import AuthHelper
from tests.helpers.data_factories import TestDataFactory

pytestmark = pytest.mark.asyncio

class TestErrorHandlingE2E:
    """Test error scenarios across the entire application"""
    
    async def test_authentication_failures(self, client: AsyncClient):
        """Test various authentication failure scenarios"""
        # 1. Invalid credentials
        response = await client.post(
            "/users/token",
            data={"username": "nonexistent@example.com", "password": "wrongpass"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 401
        
        # 2. Invalid token
        headers = AuthHelper.get_auth_headers("invalid_token")
        response = await client.get("/tasks/", headers=headers)
        assert response.status_code == 401
        
        # 3. Missing token
        response = await client.get("/tasks/")
        assert response.status_code == 401
    
    async def test_authorization_failures(self, client: AsyncClient):
        """Test authorization failures for task access"""
        # Create two users
        user1_data, user1_token = await AuthHelper.register_and_login(client)
        user2_data, user2_token = await AuthHelper.register_and_login(client)
        
        # User 1 creates a task
        task_data = TestDataFactory.create_task_data()
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
        assert response.status_code == 404
        
        # User 2 tries to update User 1's task
        update_data = TestDataFactory.create_task_update_data(title="Unauthorized Update")
        response = await client.patch(
            f"/tasks/{task_id}",
            json=update_data,
            headers=AuthHelper.get_auth_headers(user2_token)
        )
        assert response.status_code == 404
        
        # User 2 tries to delete User 1's task
        response = await client.delete(
            f"/tasks/{task_id}",
            headers=AuthHelper.get_auth_headers(user2_token)
        )
        assert response.status_code == 404
    
    async def test_validation_failures(self, client: AsyncClient):
        """Test validation failures for task operations"""
        # Register and login user
        user_data, token = await AuthHelper.register_and_login(client)
        headers = AuthHelper.get_auth_headers(token)
        
        # 1. Create task with invalid data
        invalid_task = {"title": ""}  # Missing required fields
        response = await client.post("/tasks/", json=invalid_task, headers=headers)
        assert response.status_code == 422
        
        # 2. Update task with invalid data
        task_data = TestDataFactory.create_task_data()
        response = await client.post("/tasks/", json=task_data, headers=headers)
        assert response.status_code == 201
        task_id = response.json()["id"]
        
        invalid_update = {"title": ""}  # Empty title
        response = await client.patch(f"/tasks/{task_id}", json=invalid_update, headers=headers)
        assert response.status_code == 422
    
    async def test_not_found_scenarios(self, client: AsyncClient):
        """Test not found scenarios"""
        # Register and login user
        user_data, token = await AuthHelper.register_and_login(client)
        headers = AuthHelper.get_auth_headers(token)
        
        # 1. Get non-existent task
        response = await client.get("/tasks/999999", headers=headers)
        assert response.status_code == 404
        
        # 2. Update non-existent task
        update_data = TestDataFactory.create_task_update_data(title="Update")
        response = await client.patch("/tasks/999999", json=update_data, headers=headers)
        assert response.status_code == 404
        
        # 3. Delete non-existent task
        response = await client.delete("/tasks/999999", headers=headers)
        assert response.status_code == 404
        
        # 4. Complete non-existent task
        response = await client.post("/tasks/999999/complete", headers=headers)
        assert response.status_code == 404 
