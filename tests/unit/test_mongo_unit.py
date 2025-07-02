# tests/unit/test_mongo_unit.py
from unittest.mock import MagicMock

import pytest
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.mongo import (
    connect_to_mongo,
    disconnect_from_mongo,
    ensure_indexes,
    get_tasks_collection,
)


class TestMongoFunctions:
    """Test suite for mongo.py functions"""


class TestGetTasksCollection(TestMongoFunctions):
    """Test suite for get_tasks_collection function"""

    def test_get_tasks_collection_initialized(self):
        """Test getting initialized collection"""
        mock_collection = MagicMock()

        import app.mongo

        app.mongo.tasks_collection = mock_collection

        result = get_tasks_collection()
        assert result is mock_collection

    def test_get_tasks_collection_uninitialized(self):
        """Test error when collection not initialized"""
        import app.mongo

        app.mongo.tasks_collection = None

        with pytest.raises(RuntimeError, match="not initialized"):
            get_tasks_collection()


class TestEnsureIndexes(TestMongoFunctions):
    """Test suite for ensure_indexes function"""

    @pytest.mark.asyncio
    async def test_ensure_indexes_return_if_tasks_collection_is_none(self, capsys):
        """Test index creation when collection is not initialized"""
        import app.mongo

        app.mongo.tasks_collection = None

        await ensure_indexes()

        captured = capsys.readouterr()
        assert "Tasks collection not initialized" in captured.out
        assert "skipping index creation" in captured.out

    @pytest.mark.asyncio
    async def test_ensure_indexes_fails_on_first_index(self, mocker, capsys):
        """Test exception on first index creation"""
        import app.mongo

        mock_collection = mocker.AsyncMock()
        app.mongo.tasks_collection = mock_collection

        # Raise exception immediately
        mock_collection.create_index.side_effect = Exception("Index creation failed")

        await ensure_indexes()

        captured = capsys.readouterr()
        assert "Ensuring MongoDB indexes..." in captured.out
        assert "Error creating indexes: Index creation failed" in captured.out

        # Should be called only once since it fails immediately
        assert mock_collection.create_index.call_count == 1

    @pytest.mark.asyncio
    async def test_ensure_indexes_success_creates_all_indexes(self, mocker, capsys):
        """Test successful index creation with all expected indexes"""
        from pymongo import ASCENDING, DESCENDING

        import app.mongo

        # Use AsyncMock for async methods
        mock_collection = mocker.AsyncMock()
        app.mongo.tasks_collection = mock_collection

        # Mock successful async return
        mock_collection.create_index.return_value = "index_created"

        await ensure_indexes()

        # Check that success message was printed
        captured = capsys.readouterr()
        assert "Ensuring MongoDB indexes..." in captured.out
        assert "MongoDB indexes created successfully" in captured.out

        # Verify create_index was called exactly 6 times
        assert mock_collection.create_index.call_count == 6

        # Verify the exact calls made to create_index with expected arguments
        expected_calls = [
            mocker.call([("user_id", ASCENDING)]),
            mocker.call([("created_at", DESCENDING)]),
            mocker.call([("updated_at", DESCENDING)]),
            mocker.call([("deleted_at", DESCENDING)]),
            mocker.call([("completed_at", DESCENDING)]),
            mocker.call([("user_id", ASCENDING), ("deleted_at", ASCENDING)]),
        ]

        mock_collection.create_index.assert_has_calls(expected_calls, any_order=False)


class TestConnectToMongo(TestMongoFunctions):
    """Test suite for connect_to_mongo function"""

    @pytest.mark.asyncio
    async def test_connect_to_mongo_success(self, mocker, capsys):
        """Test successful MongoDB connection"""
        import app.mongo

        # Mock AsyncMongoClient
        mock_client = mocker.AsyncMock()
        mock_db = mocker.MagicMock()
        mock_collection = mocker.MagicMock()

        # Setup mock client behavior
        mock_client.admin.command = mocker.AsyncMock(return_value={"ok": 1})
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        # Mock the AsyncMongoClient constructor
        mock_async_mongo_client = mocker.patch(
            "app.mongo.AsyncMongoClient", return_value=mock_client
        )

        # Execute the function
        await connect_to_mongo()

        # Verify console output
        captured = capsys.readouterr()
        assert f"Connecting to MongoDB at {app.mongo.MONGODB_URL}" in captured.out
        assert "Successfully connected to MongoDB" in captured.out

        # Verify AsyncMongoClient was called with correct parameters
        mock_async_mongo_client.assert_called_once_with(
            app.mongo.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            maxPoolSize=10,
            retryWrites=True,
        )

        # Verify ping command was called
        mock_client.admin.command.assert_called_once_with("ping")

        # Verify global variables were set
        assert app.mongo.mongo_client == mock_client
        assert app.mongo.db == mock_db
        assert app.mongo.tasks_collection == mock_collection

        # Verify database and collection access
        mock_client.__getitem__.assert_called_once_with(app.mongo.MONGODB_DB)
        mock_db.__getitem__.assert_called_once_with("tasks")

    @pytest.mark.asyncio
    async def test_connect_to_mongo_connection_failure(self, mocker, capsys):
        """Test MongoDB connection failure"""
        import app.mongo

        # Mock AsyncMongoClient to raise ConnectionFailure
        mock_client = mocker.AsyncMock()
        mock_client.admin.command.side_effect = ConnectionFailure("Connection refused")

        mocker.patch("app.mongo.AsyncMongoClient", return_value=mock_client)

        # Test that ConnectionFailure is raised
        with pytest.raises(ConnectionFailure, match="Connection refused"):
            await connect_to_mongo()

        # Verify console output
        captured = capsys.readouterr()
        assert f"Connecting to MongoDB at {app.mongo.MONGODB_URL}" in captured.out
        assert "Failed to connect to MongoDB: Connection refused" in captured.out
        assert "Make sure MongoDB is running and accessible" in captured.out

        # Verify ping was attempted
        mock_client.admin.command.assert_called_once_with("ping")

    @pytest.mark.asyncio
    async def test_connect_to_mongo_server_selection_timeout(self, mocker, capsys):
        """Test MongoDB server selection timeout"""
        import app.mongo

        # Mock AsyncMongoClient to raise ServerSelectionTimeoutError
        mock_client = mocker.AsyncMock()
        mock_client.admin.command.side_effect = ServerSelectionTimeoutError(
            "Server selection timeout"
        )

        mocker.patch("app.mongo.AsyncMongoClient", return_value=mock_client)

        # Test that ServerSelectionTimeoutError is raised
        with pytest.raises(
            ServerSelectionTimeoutError, match="Server selection timeout"
        ):
            await connect_to_mongo()

        # Verify console output
        captured = capsys.readouterr()
        assert f"Connecting to MongoDB at {app.mongo.MONGODB_URL}" in captured.out
        assert "Failed to connect to MongoDB: Server selection timeout" in captured.out
        assert "Make sure MongoDB is running and accessible" in captured.out

    @pytest.mark.asyncio
    async def test_connect_to_mongo_unexpected_exception(self, mocker, capsys):
        """Test unexpected exception during MongoDB connection"""
        import app.mongo

        # Mock AsyncMongoClient to raise unexpected exception
        mock_client = mocker.AsyncMock()
        mock_client.admin.command.side_effect = ValueError("Unexpected error")

        mocker.patch("app.mongo.AsyncMongoClient", return_value=mock_client)

        # Test that ValueError is raised
        with pytest.raises(ValueError, match="Unexpected error"):
            await connect_to_mongo()

        # Verify console output
        captured = capsys.readouterr()
        assert f"Connecting to MongoDB at {app.mongo.MONGODB_URL}" in captured.out
        assert (
            "Unexpected error connecting to MongoDB: Unexpected error" in captured.out
        )

    @pytest.mark.asyncio
    async def test_connect_to_mongo_client_creation_failure(self, mocker, capsys):
        """Test failure during AsyncMongoClient creation"""
        import app.mongo

        # Mock AsyncMongoClient constructor to raise exception
        mocker.patch(
            "app.mongo.AsyncMongoClient",
            side_effect=ConnectionFailure("Failed to create client"),
        )

        # Test that ConnectionFailure is raised
        with pytest.raises(ConnectionFailure, match="Failed to create client"):
            await connect_to_mongo()

        # Verify console output shows connection attempt
        captured = capsys.readouterr()
        assert f"Connecting to MongoDB at {app.mongo.MONGODB_URL}" in captured.out
        assert "Failed to connect to MongoDB: Failed to create client" in captured.out

    @pytest.mark.asyncio
    async def test_connect_to_mongo_ping_failure_with_different_error(
        self, mocker, capsys
    ):
        """Test ping command failure with different error type"""
        import app.mongo

        # Mock AsyncMongoClient
        mock_client = mocker.AsyncMock()
        # Make ping raise a different connection-related error
        mock_client.admin.command.side_effect = ServerSelectionTimeoutError(
            "No servers available"
        )

        mocker.patch("app.mongo.AsyncMongoClient", return_value=mock_client)

        # Test that ServerSelectionTimeoutError is raised
        with pytest.raises(ServerSelectionTimeoutError, match="No servers available"):
            await connect_to_mongo()

        # Verify console output
        captured = capsys.readouterr()
        assert f"Connecting to MongoDB at {app.mongo.MONGODB_URL}" in captured.out
        assert "Failed to connect to MongoDB: No servers available" in captured.out
        assert "Make sure MongoDB is running and accessible" in captured.out

    @pytest.mark.asyncio
    async def test_connect_to_mongo_globals_not_set_on_ping_failure(
        self, mocker, capsys
    ):
        """Test that global variables are not set when ping command fails"""
        import app.mongo

        # Store original values
        original_db = app.mongo.db
        original_collection = app.mongo.tasks_collection

        # Mock AsyncMongoClient to fail
        mock_client = mocker.AsyncMock()
        mock_client.admin.command.side_effect = ConnectionFailure("Connection failed")
        mocker.patch("app.mongo.AsyncMongoClient", return_value=mock_client)

        # Test connection failure
        with pytest.raises(ConnectionFailure):
            await connect_to_mongo()

        assert app.mongo.mongo_client == mock_client

        # Verify global variables were not modified
        assert app.mongo.db == original_db
        assert app.mongo.tasks_collection == original_collection

    @pytest.mark.asyncio
    async def test_connect_to_mongo_globals_not_set_on_failure(self, mocker, capsys):
        """Test that global variables are not set when connection fails"""
        import app.mongo

        # Store original values
        original_client = app.mongo.mongo_client
        original_db = app.mongo.db
        original_collection = app.mongo.tasks_collection

        # Mock AsyncMongoClient constructor to raise exception immediately
        mocker.patch(
            "app.mongo.AsyncMongoClient",
            side_effect=ConnectionFailure("Connection failed"),
        )

        # Test connection failure
        with pytest.raises(ConnectionFailure):
            await connect_to_mongo()

        # Verify global variables were not modified
        assert app.mongo.mongo_client == original_client
        assert app.mongo.db == original_db
        assert app.mongo.tasks_collection == original_collection

    @pytest.mark.asyncio
    async def test_connect_to_mongo_database_and_collection_assignment(
        self, mocker, capsys
    ):
        """Test detailed verification of database and collection assignment"""
        import app.mongo

        # Create mock objects
        mock_client = mocker.AsyncMock()
        mock_db = mocker.MagicMock()
        mock_collection = mocker.MagicMock()

        # Setup mock behavior for successful connection
        mock_client.admin.command = mocker.AsyncMock(return_value={"ok": 1})

        # Mock database access
        def mock_getitem_client(key):
            if key == app.mongo.MONGODB_DB:
                return mock_db
            return mocker.MagicMock()

        def mock_getitem_db(key):
            if key == "tasks":
                return mock_collection
            return mocker.MagicMock()

        mock_client.__getitem__.side_effect = mock_getitem_client
        mock_db.__getitem__.side_effect = mock_getitem_db

        mocker.patch("app.mongo.AsyncMongoClient", return_value=mock_client)

        # Execute function
        await connect_to_mongo()

        # Verify specific database and collection were accessed
        mock_client.__getitem__.assert_called_once_with(app.mongo.MONGODB_DB)
        mock_db.__getitem__.assert_called_once_with("tasks")

        # Verify globals are set correctly
        assert app.mongo.mongo_client is mock_client
        assert app.mongo.db is mock_db
        assert app.mongo.tasks_collection is mock_collection


class TestDisconnectFromMongo(TestMongoFunctions):
    """Test suite for disconnect_from_mongo() function"""

    @pytest.mark.asyncio
    async def test_successful_disconnection(self, mocker, capsys):
        """Test successful disconnection when client exists"""
        import app.mongo

        # Setup
        mock_client = mocker.AsyncMock()
        app.mongo.mongo_client = mock_client  # Set the global client

        # Execute
        await disconnect_from_mongo()

        # Verify
        mock_client.close.assert_awaited_once()

        # Check print output
        captured = capsys.readouterr()
        assert "Disconnected from MongoDB" in captured.out

    @pytest.mark.asyncio
    async def test_no_client_to_disconnect(self, mocker, capsys):
        """Test when no client exists to disconnect"""
        import app.mongo

        # Setup - ensure no client exists
        app.mongo.mongo_client = None

        # Execute
        await disconnect_from_mongo()

        # Verify
        captured = capsys.readouterr()
        # No message should be printed
        assert "Disconnected from MongoDB" not in captured.out

    @pytest.mark.asyncio
    async def test_close_operation_failure(self, mocker, capsys):
        """Test when close() operation fails"""
        import app.mongo

        # Setup
        mock_client = mocker.AsyncMock()
        app.mongo.mongo_client = mock_client
        mock_client.close.side_effect = Exception("Connection close failed")

        # Execute and verify exception
        with pytest.raises(Exception, match="Connection close failed"):
            await disconnect_from_mongo()

        # Verify print output
        captured = capsys.readouterr()
        assert "Disconnected from MongoDB" not in captured.out  # No success message
