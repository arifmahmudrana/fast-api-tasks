# tests/unit/conftest.py
import pytest
import sys
import os
from unittest.mock import Mock

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Mock the models and schemas modules at import time to avoid SQLAlchemy dependencies
sys.modules['app.models'] = Mock()


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables"""
    os.environ.setdefault("SECRET_KEY", "test_secret_key")
    os.environ.setdefault("ALGORITHM", "HS256")
    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")


@pytest.fixture
def mock_user_model():
    """Mock User model"""
    mock_user = Mock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.hashed_password = "$2b$12$test_hash"
    return mock_user
