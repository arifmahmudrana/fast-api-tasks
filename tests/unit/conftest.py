# tests/unit/conftest.py
import os
import sys
from unittest.mock import Mock

import pytest

# Mock the models and schemas modules at import time to avoid SQLAlchemy dependencies
sys.modules["app.models"] = Mock()


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables"""
    os.environ.setdefault("SECRET_KEY", "test_secret_key")
    os.environ.setdefault("ALGORITHM", "HS256")
    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
