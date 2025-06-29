# tests/unit/test_crud.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import os

# Import the module under test
from app import crud, models, schemas


class TestCrudFunctions:
    """Test suite for CRUD functions"""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def sample_user_create(self):
        """Sample user creation data"""
        return schemas.UserCreate(
            email="test@example.com",
            password="plaintext_password"
        )

    @pytest.fixture
    def sample_db_user(self):
        """Sample database user model"""
        user = Mock()
        user.id = 1
        user.email = "test@example.com"
        user.hashed_password = "$2b$12$hashedpassword"
        return user


class TestGetUserByEmail(TestCrudFunctions):
    """Tests for get_user_by_email function"""

    def test_get_user_by_email_found(self, mock_db_session, sample_db_user):
        """Test getting user by email when user exists"""
        # Arrange
        email = "test@example.com"
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_db_user
        mock_db_session.query.return_value = mock_query

        # Act
        result = crud.get_user_by_email(mock_db_session, email)

        # Assert
        assert result == sample_db_user
        mock_db_session.query.assert_called_once_with(models.User)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()

    def test_get_user_by_email_not_found(self, mock_db_session):
        """Test getting user by email when user doesn't exist"""
        # Arrange
        email = "nonexistent@example.com"
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        mock_db_session.query.return_value = mock_query

        # Act
        result = crud.get_user_by_email(mock_db_session, email)

        # Assert
        assert result is None
        mock_db_session.query.assert_called_once_with(models.User)

    def test_get_user_by_email_with_special_characters(self, mock_db_session):
        """Test getting user by email with special characters"""
        # Arrange
        email = "test+tag@example-domain.co.uk"
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        mock_db_session.query.return_value = mock_query

        # Act
        result = crud.get_user_by_email(mock_db_session, email)

        # Assert
        assert result is None
        mock_db_session.query.assert_called_once_with(models.User)


class TestCreateUser(TestCrudFunctions):
    """Tests for create_user function"""

    @patch('app.crud.pwd_context')
    @patch('app.crud.models.User')
    def test_create_user_success(self, mock_user_model, mock_pwd_context,
                                 mock_db_session, sample_user_create):
        """Test successful user creation"""
        # Arrange
        hashed_password = "$2b$12$hashedpassword"
        mock_pwd_context.hash.return_value = hashed_password

        mock_db_user = Mock()
        mock_db_user.id = 1
        mock_db_user.email = sample_user_create.email
        mock_user_model.return_value = mock_db_user

        # Act
        result = crud.create_user(mock_db_session, sample_user_create)

        # Assert
        assert result == mock_db_user
        mock_pwd_context.hash.assert_called_once_with(
            sample_user_create.password)
        mock_user_model.assert_called_once_with(
            email=sample_user_create.email,
            hashed_password=hashed_password
        )
        mock_db_session.add.assert_called_once_with(mock_db_user)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_db_user)

    @patch('app.crud.pwd_context')
    @patch('app.crud.models.User')
    def test_create_user_with_long_email(self, mock_user_model, mock_pwd_context,
                                         mock_db_session):
        """Test user creation with long email"""
        # Arrange
        long_email = "a" * 50 + "@example.com"
        user_data = schemas.UserCreate(
            email=long_email, password="password123")
        hashed_password = "$2b$12$hashedpassword"
        mock_pwd_context.hash.return_value = hashed_password

        mock_db_user = Mock()
        mock_user_model.return_value = mock_db_user

        # Act
        result = crud.create_user(mock_db_session, user_data)

        # Assert
        assert result == mock_db_user
        mock_pwd_context.hash.assert_called_once_with("password123")
        mock_user_model.assert_called_once_with(
            email=long_email,
            hashed_password=hashed_password
        )

    @patch('app.crud.pwd_context')
    @patch('app.crud.models.User')
    def test_create_user_database_error(self, mock_user_model, mock_pwd_context,
                                        mock_db_session, sample_user_create):
        """Test user creation when database commit fails"""
        # Arrange
        hashed_password = "$2b$12$hashedpassword"
        mock_pwd_context.hash.return_value = hashed_password

        mock_db_user = Mock()
        mock_user_model.return_value = mock_db_user
        mock_db_session.commit.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            crud.create_user(mock_db_session, sample_user_create)

        # Verify the user was added before the error
        mock_db_session.add.assert_called_once_with(mock_db_user)
        mock_db_session.commit.assert_called_once()


class TestAuthenticateUser(TestCrudFunctions):
    """Tests for authenticate_user function"""

    @patch('app.crud.get_user_by_email')
    @patch('app.crud.pwd_context')
    def test_authenticate_user_success(self, mock_pwd_context, mock_get_user,
                                       mock_db_session, sample_db_user):
        """Test successful user authentication"""
        # Arrange
        email = "test@example.com"
        password = "correct_password"
        mock_get_user.return_value = sample_db_user
        mock_pwd_context.verify.return_value = True

        # Act
        result = crud.authenticate_user(mock_db_session, email, password)

        # Assert
        assert result == sample_db_user
        mock_get_user.assert_called_once_with(mock_db_session, email)
        mock_pwd_context.verify.assert_called_once_with(
            password, sample_db_user.hashed_password
        )

    @patch('app.crud.get_user_by_email')
    @patch('app.crud.pwd_context')
    def test_authenticate_user_wrong_password(self, mock_pwd_context, mock_get_user,
                                              mock_db_session, sample_db_user):
        """Test authentication with wrong password"""
        # Arrange
        email = "test@example.com"
        password = "wrong_password"
        mock_get_user.return_value = sample_db_user
        mock_pwd_context.verify.return_value = False

        # Act
        result = crud.authenticate_user(mock_db_session, email, password)

        # Assert
        assert result is False
        mock_get_user.assert_called_once_with(mock_db_session, email)
        mock_pwd_context.verify.assert_called_once_with(
            password, sample_db_user.hashed_password
        )

    @patch('app.crud.get_user_by_email')
    @patch('app.crud.pwd_context')
    def test_authenticate_user_not_found(self, mock_pwd_context, mock_get_user,
                                         mock_db_session):
        """Test authentication when user doesn't exist"""
        # Arrange
        email = "nonexistent@example.com"
        password = "any_password"
        mock_get_user.return_value = None

        # Act
        result = crud.authenticate_user(mock_db_session, email, password)

        # Assert
        assert result is False
        mock_get_user.assert_called_once_with(mock_db_session, email)
        mock_pwd_context.verify.assert_not_called()

    @patch('app.crud.get_user_by_email')
    @patch('app.crud.pwd_context')
    def test_authenticate_user_empty_password(self, mock_pwd_context, mock_get_user,
                                              mock_db_session, sample_db_user):
        """Test authentication with empty password"""
        # Arrange
        email = "test@example.com"
        password = ""
        mock_get_user.return_value = sample_db_user
        mock_pwd_context.verify.return_value = False

        # Act
        result = crud.authenticate_user(mock_db_session, email, password)

        # Assert
        assert result is False
        mock_pwd_context.verify.assert_called_once_with(
            "", sample_db_user.hashed_password)


class TestPasswordHashing(TestCrudFunctions):
    """Tests for password hashing configuration"""

    def test_pwd_context_configuration(self):
        """Test that password context is properly configured"""
        # Test that the context uses bcrypt
        assert "bcrypt" in crud.pwd_context.schemes()

    def test_password_hashing_and_verification(self):
        """Integration test for password hashing and verification"""
        password = "test_password_123"

        # Hash the password
        hashed = crud.pwd_context.hash(password)

        # Verify it's actually hashed (different from original)
        assert hashed != password
        assert hashed.startswith("$2b$")

        # Verify the password
        assert crud.pwd_context.verify(password, hashed) is True
        assert crud.pwd_context.verify("wrong_password", hashed) is False


class TestEnvironmentVariables(TestCrudFunctions):
    """Tests for environment variable handling"""

    def test_default_values(self):
        """Test that default values are set correctly"""
        # These should work even without environment variables
        assert crud.SECRET_KEY is not None
        assert crud.ALGORITHM is not None
        assert crud.ACCESS_TOKEN_EXPIRE_MINUTES is not None
        assert isinstance(crud.ACCESS_TOKEN_EXPIRE_MINUTES, int)

    @patch.dict(os.environ, {
        'SECRET_KEY': 'test_secret',
        'ALGORITHM': 'HS512',
        'ACCESS_TOKEN_EXPIRE_MINUTES': '60'
    })
    def test_environment_variable_override(self):
        """Test that environment variables override defaults"""
        # Need to reimport to get new environment values
        import importlib
        importlib.reload(crud)

        assert crud.SECRET_KEY == 'test_secret'
        assert crud.ALGORITHM == 'HS512'
        assert crud.ACCESS_TOKEN_EXPIRE_MINUTES == 60


# Integration test class
class TestCrudIntegration(TestCrudFunctions):
    """Integration tests that test multiple functions together"""

    @patch('app.crud.pwd_context')
    @patch('app.crud.models.User')
    def test_create_and_authenticate_user_flow(self, mock_user_model, mock_pwd_context,
                                               mock_db_session):
        """Test the complete flow of creating and then authenticating a user"""
        # Arrange
        email = "integration@example.com"
        password = "test_password"
        hashed_password = "$2b$12$integration_hash"

        user_create = schemas.UserCreate(email=email, password=password)
        mock_pwd_context.hash.return_value = hashed_password
        mock_pwd_context.verify.return_value = True

        # Create mock user
        mock_db_user = Mock()
        mock_db_user.email = email
        mock_db_user.hashed_password = hashed_password
        mock_user_model.return_value = mock_db_user

        # Mock the query chain for get_user_by_email
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_db_user
        mock_db_session.query.return_value = mock_query

        # Act - Create user
        created_user = crud.create_user(mock_db_session, user_create)

        # Act - Authenticate user
        authenticated_user = crud.authenticate_user(
            mock_db_session, email, password)

        # Assert
        assert created_user == mock_db_user
        assert authenticated_user == mock_db_user
        mock_pwd_context.hash.assert_called_once_with(password)
        mock_pwd_context.verify.assert_called_once_with(
            password, hashed_password)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
