# tests/unit/conftest.py
import pytest
import sys
import os
from unittest.mock import Mock

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Mock the models and schemas modules at import time to avoid SQLAlchemy dependencies
sys.modules['app.models'] = Mock()
# sys.modules['app.schemas'] = Mock()


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


@pytest.fixture
def mock_database_components():
    """Fixture providing mocked database components"""
    with patch('app.database.create_engine') as mock_engine, \
            patch('app.database.sessionmaker') as mock_sessionmaker, \
            patch('app.database.declarative_base') as mock_base, \
            patch('app.database.load_dotenv') as mock_load_dotenv:

        # Setup return values
        mock_engine_instance = Mock()
        mock_engine.return_value = mock_engine_instance

        mock_session_class = Mock()
        mock_sessionmaker.return_value = mock_session_class

        mock_base_instance = Mock()
        mock_base.return_value = mock_base_instance

        yield {
            'engine': mock_engine,
            'engine_instance': mock_engine_instance,
            'sessionmaker': mock_sessionmaker,
            'session_class': mock_session_class,
            'base': mock_base,
            'base_instance': mock_base_instance,
            'load_dotenv': mock_load_dotenv
        }


@pytest.fixture
def database_urls():
    """Fixture providing various database URL examples"""
    return {
        'sqlite_file': 'sqlite:///test.db',
        'sqlite_memory': 'sqlite:///:memory:',
        'postgresql': 'postgresql://user:password@localhost:5432/testdb',
        'mysql': 'mysql://user:password@localhost:3306/testdb',
        'invalid': 'invalid://connection/string',
        'empty': '',
        'none': None
    }


@pytest.fixture(autouse=True)
def reset_database_module():
    """Automatically reset the database module for each test"""
    # This ensures that module-level imports don't interfere between tests
    if 'app.database' in sys.modules:
        # Store reference to avoid issues during cleanup
        db_module = sys.modules['app.database']
        yield
        # Module will be reloaded in individual tests as needed
    else:
        yield


@pytest.fixture
def temp_env_vars():
    """Fixture for temporarily setting environment variables"""
    def _set_env_vars(**kwargs):
        original_values = {}
        for key, value in kwargs.items():
            original_values[key] = os.environ.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        return original_values

    return _set_env_vars
