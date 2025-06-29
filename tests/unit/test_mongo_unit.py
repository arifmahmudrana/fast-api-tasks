# tests/unit/test_mongo_unit.py
import pytest
from unittest.mock import MagicMock
from app import mongo


class TestMongoFunctions:
    """Test suite for mongo.py functions"""


class TestGetTasksCollection(TestMongoFunctions):
    """Test suite for get_tasks_collection function"""

    def test_get_tasks_collection_initialized(self):
        """Test getting initialized collection"""
        mock_collection = MagicMock()
        mongo.tasks_collection = mock_collection

        assert mongo.get_tasks_collection() is mock_collection

    def test_get_tasks_collection_uninitialized(self):
        """Test error when collection not initialized"""
        mongo.tasks_collection = None

        with pytest.raises(RuntimeError, match="not initialized"):
            mongo.get_tasks_collection()
