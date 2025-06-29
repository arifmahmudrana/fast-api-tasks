# tests/unit/test_deps_unit.py
import pytest
from fastapi import HTTPException
from jose import JWTError
from app.deps import get_db, get_current_user
from app import crud

# Mock data for testing
TEST_SECRET_KEY = "test-secret-key"
TEST_ALGORITHM = "HS256"
TEST_EMAIL = "test@example.com"
TEST_TOKEN = "test-token"
TEST_PAYLOAD = {"sub": TEST_EMAIL}


def test_get_db(mocker):
    # Mock the database session
    mock_session_local = mocker.patch('app.database.SessionLocal')
    mock_db = mocker.MagicMock()
    mock_session_local.return_value = mock_db

    # Test that get_db yields a session and closes it
    generator = get_db()
    db = next(generator)

    assert db == mock_db
    # Test that the db is closed after use
    try:
        next(generator)
    except StopIteration:
        pass

    mock_db.close.assert_called_once()


def test_get_current_user_valid_token(mocker):
    # Setup mocks
    mocker.patch.object(crud, 'SECRET_KEY', TEST_SECRET_KEY)
    mocker.patch.object(crud, 'ALGORITHM', TEST_ALGORITHM)

    # Patch the jwt.decode call WHERE IT'S USED (in deps.py)
    mock_jwt_decode = mocker.patch(
        'app.deps.jwt.decode', return_value=TEST_PAYLOAD)

    mock_get_user = mocker.patch('app.crud.get_user_by_email')
    mock_user = mocker.MagicMock()
    mock_get_user.return_value = mock_user

    # Mock DB dependency
    mock_db = mocker.MagicMock()

    # Call the function
    result = get_current_user(token=TEST_TOKEN, db=mock_db)

    # Assertions
    mock_jwt_decode.assert_called_once_with(
        TEST_TOKEN, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM]
    )
    mock_get_user.assert_called_once_with(mock_db, email=TEST_EMAIL)
    assert result == mock_user


def test_get_current_user_invalid_token(mocker):
    # Setup mocks
    mocker.patch.object(crud, 'SECRET_KEY', TEST_SECRET_KEY)
    mocker.patch.object(crud, 'ALGORITHM', TEST_ALGORITHM)

    mocker.patch('app.deps.jwt.decode', side_effect=JWTError("Invalid token"))

    # Mock DB dependency
    mock_db = mocker.MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="invalid-token", db=mock_db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


def test_get_current_user_missing_email(mocker):
    # Setup mocks
    mocker.patch.object(crud, 'SECRET_KEY', TEST_SECRET_KEY)
    mocker.patch.object(crud, 'ALGORITHM', TEST_ALGORITHM)

    mocker.patch('app.deps.jwt.decode', return_value={"sub": None})

    # Mock DB dependency
    mock_db = mocker.MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=TEST_TOKEN, db=mock_db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


def test_get_current_user_nonexistent_user(mocker):
    # Setup mocks
    mocker.patch.object(crud, 'SECRET_KEY', TEST_SECRET_KEY)
    mocker.patch.object(crud, 'ALGORITHM', TEST_ALGORITHM)

    mocker.patch('app.deps.jwt.decode', return_value=TEST_PAYLOAD)
    mocker.patch('app.crud.get_user_by_email', return_value=None)

    # Mock DB dependency
    mock_db = mocker.MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=TEST_TOKEN, db=mock_db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"
