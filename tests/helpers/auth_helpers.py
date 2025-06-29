# tests/helpers/auth_helpers.py
import uuid
from typing import Dict, Tuple, Optional


class AuthHelper:
    @staticmethod
    def create_user_data(unique_suffix: Optional[str] = None) -> Dict[str, str]:
        """Create test user data with unique email"""
        suffix = unique_suffix or str(uuid.uuid4())[:8]
        return {
            "email": f"test_{suffix}@example.com",
            "password": "testpass123"
        }

    @staticmethod
    def get_auth_headers(token: str) -> Dict[str, str]:
        """Get authorization headers with Bearer token"""
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    async def register_and_login(client, user_data: Optional[Dict[str, str]] = None) -> Tuple[Dict[str, str], str]:
        """Helper to register and login user"""
        if not user_data:
            user_data = AuthHelper.create_user_data()

        # Register
        register_response = await client.post("/users/register", json=user_data)
        assert register_response.status_code in (
            200, 400), f"Registration failed: {register_response.text}"

        # Login
        token_response = await client.post(
            "/users/token",
            data={"username": user_data["email"],
                  "password": user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert token_response.status_code == 200, f"Login failed: {token_response.text}"

        token = token_response.json()["access_token"]
        return user_data, token
