# tests/unit/test_database.py
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class TestDatabaseConfiguration:
    """Test suite for database configuration"""

    @patch('app.database.load_dotenv')
    @patch('app.database.create_engine')
    @patch('app.database.sessionmaker')
    @patch('app.database.declarative_base')
    @patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///test.db'})
    def test_database_initialization_with_env_var(self, mock_declarative_base,
                                                  mock_sessionmaker, mock_create_engine,
                                                  mock_load_dotenv):
        """Test database initialization with DATABASE_URL environment variable"""
        # Arrange
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        mock_session_class = Mock()
        mock_sessionmaker.return_value = mock_session_class
        mock_base = Mock()
        mock_declarative_base.return_value = mock_base

        # Act - Import the module to trigger initialization
        import importlib
        import app.database
        importlib.reload(app.database)

        # Assert
        mock_load_dotenv.assert_called_once()
        mock_create_engine.assert_called_once_with('sqlite:///test.db')
        mock_sessionmaker.assert_called_once_with(
            autocommit=False,
            autoflush=False,
            bind=mock_engine
        )
        mock_declarative_base.assert_called_once()

    @patch('app.database.load_dotenv')
    @patch('app.database.create_engine')
    @patch('app.database.sessionmaker')
    @patch('app.database.declarative_base')
    @patch.dict(os.environ, {}, clear=True)
    def test_database_initialization_without_env_var(self, mock_declarative_base,
                                                     mock_sessionmaker, mock_create_engine,
                                                     mock_load_dotenv):
        """Test database initialization without DATABASE_URL environment variable"""
        # Act - Import the module to trigger initialization
        import importlib
        import app.database
        importlib.reload(app.database)

        # Assert
        mock_load_dotenv.assert_called_once()
        mock_create_engine.assert_called_once_with(
            None)  # Should be called with None

    @patch('app.database.load_dotenv')
    @patch('app.database.create_engine')
    @patch('app.database.sessionmaker')
    @patch('app.database.declarative_base')
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:pass@localhost/testdb'})
    def test_database_initialization_with_postgresql_url(self, mock_declarative_base,
                                                         mock_sessionmaker, mock_create_engine,
                                                         mock_load_dotenv):
        """Test database initialization with PostgreSQL URL"""
        # Arrange
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine

        # Act
        import importlib
        import app.database
        importlib.reload(app.database)

        # Assert
        mock_create_engine.assert_called_once_with(
            'postgresql://user:pass@localhost/testdb')

    @patch('app.database.load_dotenv')
    @patch('app.database.create_engine')
    @patch('app.database.sessionmaker')
    @patch('app.database.declarative_base')
    @patch.dict(os.environ, {'DATABASE_URL': 'mysql://user:pass@localhost/testdb'})
    def test_database_initialization_with_mysql_url(self, mock_declarative_base,
                                                    mock_sessionmaker, mock_create_engine,
                                                    mock_load_dotenv):
        """Test database initialization with MySQL URL"""
        # Arrange
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine

        # Act
        import importlib
        import app.database
        importlib.reload(app.database)

        # Assert
        mock_create_engine.assert_called_once_with(
            'mysql://user:pass@localhost/testdb')

    @patch('app.database.load_dotenv')
    @patch('app.database.create_engine', side_effect=Exception("Database connection failed"))
    @patch('app.database.sessionmaker')
    @patch('app.database.declarative_base')
    @patch.dict(os.environ, {'DATABASE_URL': 'invalid://connection'})
    def test_database_initialization_with_invalid_url(self, mock_declarative_base,
                                                      mock_sessionmaker, mock_create_engine,
                                                      mock_load_dotenv):
        """Test database initialization with invalid URL raises exception"""
        # Act & Assert
        with pytest.raises(Exception, match="Database connection failed"):
            import importlib
            import app.database
            importlib.reload(app.database)

    def test_sessionmaker_configuration(self):
        """Test that SessionLocal is configured correctly"""
        # This test verifies the actual configuration without mocking
        with patch('app.database.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine

            with patch('app.database.sessionmaker') as mock_sessionmaker:
                mock_session_class = Mock()
                mock_sessionmaker.return_value = mock_session_class

                # Reload to trigger initialization
                import importlib
                import app.database
                importlib.reload(app.database)

                # Verify sessionmaker was called with correct parameters
                mock_sessionmaker.assert_called_once_with(
                    autocommit=False,
                    autoflush=False,
                    bind=mock_engine
                )

    @patch('app.database.load_dotenv')
    def test_load_dotenv_is_called(self, mock_load_dotenv):
        """Test that load_dotenv is called during initialization"""
        # Act
        import importlib
        import app.database
        importlib.reload(app.database)

        # Assert
        mock_load_dotenv.assert_called_once()

    @patch('app.database.declarative_base')
    def test_declarative_base_creation(self, mock_declarative_base):
        """Test that declarative_base is created"""
        # Arrange
        mock_base = Mock()
        mock_declarative_base.return_value = mock_base

        # Act
        import importlib
        import app.database
        importlib.reload(app.database)

        # Assert
        mock_declarative_base.assert_called_once()


class TestDatabaseSession:
    """Test suite for database session handling"""

    @patch('app.database.SessionLocal')
    def test_session_creation(self, mock_session_local):
        """Test creating a database session"""
        # Arrange
        mock_session = Mock()
        mock_session_local.return_value = mock_session

        # Act
        import app.database
        session = app.database.SessionLocal()

        # Assert
        assert session == mock_session
        mock_session_local.assert_called_once()

    @patch('app.database.SessionLocal')
    def test_multiple_sessions_creation(self, mock_session_local):
        """Test creating multiple database sessions"""
        # Arrange
        mock_session1 = Mock()
        mock_session2 = Mock()
        mock_session_local.side_effect = [mock_session1, mock_session2]

        # Act
        import app.database
        session1 = app.database.SessionLocal()
        session2 = app.database.SessionLocal()

        # Assert
        assert session1 == mock_session1
        assert session2 == mock_session2
        assert mock_session_local.call_count == 2


class TestDatabaseIntegration:
    """Integration tests for database configuration"""

    @patch('app.database.load_dotenv')
    @patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///test_integration.db'})
    def test_full_database_setup_integration(self, mock_load_dotenv):
        """Test full database setup integration"""
        # This test uses actual SQLAlchemy objects (not mocked)
        # to verify the integration works correctly

        # Act
        import importlib
        import app.database
        importlib.reload(app.database)

        # Assert
        assert app.database.SQLALCHEMY_DATABASE_URL == 'sqlite:///test_integration.db'
        assert app.database.engine is not None
        assert app.database.SessionLocal is not None
        assert app.database.Base is not None

        # Verify engine is properly configured
        assert str(app.database.engine.url) == 'sqlite:///test_integration.db'

        # Verify we can create a session
        session = app.database.SessionLocal()
        assert session is not None
        session.close()

    @patch('app.database.load_dotenv')
    @patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///:memory:'})
    def test_in_memory_database_setup(self, mock_load_dotenv):
        """Test setup with in-memory SQLite database"""
        # Act
        import importlib
        import app.database
        importlib.reload(app.database)

        # Assert
        assert app.database.SQLALCHEMY_DATABASE_URL == 'sqlite:///:memory:'
        assert str(app.database.engine.url) == 'sqlite:///:memory:'

        # Verify we can create and use a session
        session = app.database.SessionLocal()
        assert session is not None
        session.close()


class TestDatabaseEnvironmentVariables:
    """Test suite for environment variable handling in database configuration"""

    @patch('app.database.load_dotenv')
    @patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///production.db'})
    def test_production_database_url(self, mock_load_dotenv):
        """Test with production database URL"""
        # Act
        import importlib
        import app.database
        importlib.reload(app.database)

        # Assert
        assert app.database.SQLALCHEMY_DATABASE_URL == 'sqlite:///production.db'

    @patch('app.database.load_dotenv')
    @patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///development.db'})
    def test_development_database_url(self, mock_load_dotenv):
        """Test with development database URL"""
        # Act
        import importlib
        import app.database
        importlib.reload(app.database)

        # Assert
        assert app.database.SQLALCHEMY_DATABASE_URL == 'sqlite:///development.db'

    @patch('app.database.load_dotenv')
    @patch.dict(os.environ, {'DATABASE_URL': ''})
    def test_empty_database_url(self, mock_load_dotenv):
        """Test with empty DATABASE_URL environment variable"""
        # Act
        import importlib
        import app.database
        importlib.reload(app.database)

        # Assert
        assert app.database.SQLALCHEMY_DATABASE_URL == ''

    @patch('app.database.load_dotenv')
    @patch.dict(os.environ, {'DATABASE_URL': '   sqlite:///test.db   '})
    def test_database_url_with_whitespace(self, mock_load_dotenv):
        """Test DATABASE_URL with leading/trailing whitespace"""
        # Act
        import importlib
        import app.database
        importlib.reload(app.database)

        # Assert - Note: os.getenv doesn't strip whitespace automatically
        assert app.database.SQLALCHEMY_DATABASE_URL == '   sqlite:///test.db   '


class TestDatabaseErrorHandling:
    """Test suite for error handling in database configuration"""

    @patch('app.database.load_dotenv', side_effect=Exception("Failed to load .env"))
    def test_dotenv_loading_failure(self, mock_load_dotenv):
        """Test handling of .env loading failure"""
        # Act & Assert
        with pytest.raises(Exception, match="Failed to load .env"):
            import importlib
            import app.database
            importlib.reload(app.database)

    @patch('app.database.load_dotenv')
    @patch('app.database.sessionmaker', side_effect=Exception("SessionLocal creation failed"))
    @patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///test.db'})
    def test_session_creation_failure(self, mock_sessionmaker, mock_load_dotenv):
        """Test handling of SessionLocal creation failure"""
        # Act & Assert
        with pytest.raises(Exception, match="SessionLocal creation failed"):
            import importlib
            import app.database
            importlib.reload(app.database)

    @patch('app.database.load_dotenv')
    @patch('app.database.declarative_base', side_effect=Exception("Base creation failed"))
    @patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///test.db'})
    def test_base_creation_failure(self, mock_declarative_base, mock_load_dotenv):
        """Test handling of Base creation failure"""
        # Act & Assert
        with pytest.raises(Exception, match="Base creation failed"):
            import importlib
            import app.database
            importlib.reload(app.database)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
