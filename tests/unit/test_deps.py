# tests/unit/test_deps.py
import pytest
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from unittest.mock import MagicMock, patch

from app.deps import get_db, get_current_user
from app import crud

# Mock data for testing
TEST_SECRET_KEY = "test-secret-key"
TEST_ALGORITHM = "HS256"
TEST_EMAIL = "test@example.com"
TEST_TOKEN = "test-token"
TEST_PAYLOAD = {"sub": TEST_EMAIL}


@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def mock_oauth2_scheme():
    scheme = MagicMock(spec=OAuth2PasswordBearer)
    return scheme


def test_get_db():
    # Test that get_db yields a session and closes it
    with patch('app.database.SessionLocal') as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        generator = get_db()
        db = next(generator)

        assert db == mock_db
        # Test that the db is closed after use
        try:
            next(generator)
        except StopIteration:
            pass

        mock_db.close.assert_called_once()


@patch('app.crud.SECRET_KEY', TEST_SECRET_KEY)
@patch('app.crud.ALGORITHM', TEST_ALGORITHM)
def test_get_current_user_valid_token(mock_db, mock_oauth2_scheme):
    # Test with valid token and existing user
    mock_oauth2_scheme.return_value = TEST_TOKEN

    with patch('jwt.decode') as mock_jwt_decode, \
            patch('app.crud.get_user_by_email') as mock_get_user:

        # Setup mocks
        mock_jwt_decode.return_value = TEST_PAYLOAD
        mock_user = MagicMock()
        mock_get_user.return_value = mock_user

        # Call the function
        result = get_current_user(token=TEST_TOKEN, db=mock_db)

        # Assertions
        mock_jwt_decode.assert_called_once_with(
            TEST_TOKEN, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM]
        )
        mock_get_user.assert_called_once_with(mock_db, email=TEST_EMAIL)
        assert result == mock_user


@patch('app.crud.SECRET_KEY', TEST_SECRET_KEY)
@patch('app.crud.ALGORITHM', TEST_ALGORITHM)
def test_get_current_user_invalid_token(mock_db):
    # Test with invalid token (JWTError)
    with patch('jwt.decode') as mock_jwt_decode:
        mock_jwt_decode.side_effect = JWTError("Invalid token")

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token="invalid-token", db=mock_db)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"


@patch('app.crud.SECRET_KEY', TEST_SECRET_KEY)
@patch('app.crud.ALGORITHM', TEST_ALGORITHM)
def test_get_current_user_missing_email(mock_db):
    # Test with token missing email
    with patch('jwt.decode') as mock_jwt_decode:
        mock_jwt_decode.return_value = {"sub": None}

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=TEST_TOKEN, db=mock_db)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"


@patch('app.crud.SECRET_KEY', TEST_SECRET_KEY)
@patch('app.crud.ALGORITHM', TEST_ALGORITHM)
def test_get_current_user_nonexistent_user(mock_db):
    # Test with valid token but user doesn't exist in DB
    with patch('jwt.decode') as mock_jwt_decode, \
            patch('app.crud.get_user_by_email') as mock_get_user:

        mock_jwt_decode.return_value = TEST_PAYLOAD
        mock_get_user.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=TEST_TOKEN, db=mock_db)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"
        mock_get_user.assert_called_once_with(mock_db, email=TEST_EMAIL)
