# tests/unit/test_database_unit.py
import pytest
import os
from unittest.mock import patch, MagicMock
import sys


class TestDatabaseInitialization:
    """Test database initialization"""

    @patch('app.database.load_dotenv')
    @patch('app.database.create_engine')
    @patch('app.database.sessionmaker')
    @patch('app.database.declarative_base')
    def test_init_db(self, mock_base, mock_sessionmaker, mock_engine, mock_dotenv):
        """Test database initialization"""
        # Setup mocks
        mock_engine_instance = MagicMock()
        mock_engine.return_value = mock_engine_instance
        mock_session_class = MagicMock()
        mock_sessionmaker.return_value = mock_session_class
        mock_base_instance = MagicMock()
        mock_base.return_value = mock_base_instance

        # Test with env var
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///test.db'}):
            from app.database import init_db
            engine, SessionLocal, Base = init_db()

            mock_dotenv.assert_called_once()
            mock_engine.assert_called_once_with('sqlite:///test.db')
            mock_sessionmaker.assert_called_once_with(
                autocommit=False,
                autoflush=False,
                bind=mock_engine_instance
            )
            mock_base.assert_called_once()

    @patch('app.database.create_engine', side_effect=Exception("DB error"))
    def test_init_db_failure(self, mock_engine):
        """Test initialization failure"""
        with patch.dict(os.environ, {'DATABASE_URL': 'invalid://url'}):
            from app.database import init_db
            with pytest.raises(Exception, match="DB error"):
                init_db()


class TestDatabaseComponents:
    """Test database components"""

    def test_session_creation(self):
        """Test session creation"""
        with patch('app.database.SessionLocal') as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value = mock_session_instance

            from app.database import SessionLocal
            session = SessionLocal()

            assert session == mock_session_instance
            mock_session.assert_called_once()


class TestDatabaseURLHandling:
    """Test database URL handling"""

    @patch('app.database.create_engine')
    def test_empty_url(self, mock_engine):
        """Test empty database URL"""
        with patch.dict(os.environ, {'DATABASE_URL': ''}):
            from app.database import init_db
            with pytest.raises(ValueError, match="DATABASE_URL environment variable is not set or is empty"):
                init_db()
            mock_engine.assert_not_called()

    @patch('app.database.create_engine')
    def test_whitespace_url(self, mock_engine):
        """Test URL with whitespace"""
        with patch.dict(os.environ, {'DATABASE_URL': '  sqlite:///test.db  '}):
            from app.database import init_db
            engine, _, _ = init_db()
            mock_engine.assert_called_once_with('sqlite:///test.db')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
