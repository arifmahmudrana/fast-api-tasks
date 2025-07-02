# tests/unit/routers/test_users_unit.py
import pytest
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app import crud, schemas
from app.routers.users import router


@pytest.fixture
def mock_db(mocker):
    """Fixture for mocking database session"""
    return mocker.MagicMock()


@pytest.fixture
def mock_user():
    """Fixture for mock user data"""
    return schemas.User(id=1, email="test@example.com")


@pytest.fixture
def mock_user_create():
    """Fixture for mock user creation data"""
    return schemas.UserCreate(email="test@example.com", password="password")


@pytest.fixture
def mock_token():
    """Fixture for mock token data"""
    return {"access_token": "fake_token", "token_type": "bearer"}


def test_register_user_success(mocker, mock_db, mock_user, mock_user_create):
    """Test successful user registration"""
    # Arrange
    mocker.patch.object(crud, "get_user_by_email", return_value=None)
    mocker.patch.object(crud, "create_user", return_value=mock_user)

    # Act
    response = router.routes[0].endpoint(user=mock_user_create, db=mock_db)

    # Assert
    crud.get_user_by_email.assert_called_once_with(mock_db, email="test@example.com")
    crud.create_user.assert_called_once_with(db=mock_db, user=mock_user_create)
    assert response == mock_user


def test_register_user_email_exists(mocker, mock_db, mock_user_create):
    """Test registration with existing email"""
    # Arrange
    # Mock get_user_by_email to return a user (simulating existing user)
    mocker.patch(
        "app.crud.get_user_by_email",
        return_value=schemas.User(id=1, email="test@example.com", is_active=True),
    )

    # Create a mock for create_user (important!)
    create_user_mock = mocker.patch("app.crud.create_user")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        router.routes[0].endpoint(user=mock_user_create, db=mock_db)

    # Verify the exception
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Email already registered"

    # Verify get_user_by_email was called
    crud.get_user_by_email.assert_called_once_with(mock_db, email="test@example.com")

    # Verify create_user was NOT called
    create_user_mock.assert_not_called()  # Now this works!


def test_login_for_access_token_success(mocker, mock_db, mock_user, mock_token):
    """Test successful token generation"""
    # Arrange
    form_data = OAuth2PasswordRequestForm(
        username="test@example.com", password="password", scope=""
    )
    mocker.patch("app.crud.authenticate_user", return_value=mock_user)
    mocker.patch("app.crud.create_access_token", return_value="fake_token")

    # Act
    response = router.routes[1].endpoint(form_data=form_data, db=mock_db)

    # Assert
    crud.authenticate_user.assert_called_once_with(
        mock_db, "test@example.com", "password"
    )
    crud.create_access_token.assert_called_once_with(data={"sub": "test@example.com"})
    assert response == mock_token


def test_login_for_access_token_invalid_credentials(mocker, mock_db):
    """Test login with invalid credentials"""
    # Arrange
    form_data = OAuth2PasswordRequestForm(
        username="test@example.com", password="wrong", scope=""
    )
    mocker.patch("app.crud.authenticate_user", return_value=None)
    mocker.patch("app.crud.create_access_token")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        router.routes[1].endpoint(form_data=form_data, db=mock_db)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Incorrect username or password"
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
    crud.authenticate_user.assert_called_once_with(mock_db, "test@example.com", "wrong")
    crud.create_access_token.assert_not_called()


def test_login_for_access_token_empty_username(mocker, mock_db):
    """Test login with empty username"""
    # Arrange
    form_data = OAuth2PasswordRequestForm(username="", password="password", scope="")
    mocker.patch("app.crud.authenticate_user", return_value=None)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        router.routes[1].endpoint(form_data=form_data, db=mock_db)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    crud.authenticate_user.assert_called_once_with(mock_db, "", "password")
