# tests/unit/routers/test_tasks_unit.py
import pytest
from datetime import datetime, UTC
from bson import ObjectId
from fastapi import HTTPException
from app.routers.tasks import (
    create_task,
    list_tasks,
    get_task,
    update_task,
    delete_task,
    mark_complete,
    mark_uncomplete,
)
from app.schemas_task import TaskCreate, TaskUpdate, TaskInDB, TaskList
import app.schemas as schemas


class TestTaskBase:
    """Base class to test tasks endpoint"""

    @pytest.fixture
    def mock_user(self):
        return schemas.User(id=1, email="test@example.com")

    @pytest.fixture
    def task_create(self):
        return TaskCreate(title="Test Task", description="Test Description")

    @pytest.fixture
    def mock_now(self, mocker):
        now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        mocker.patch("app.routers.tasks.datetime").now.return_value = now
        return now

    @pytest.fixture
    def mock_tasks_data(self):
        return [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "user_id": 1,
                "title": "Task 1",
                "description": "Description 1",
                "created_at": datetime(2023, 1, 1, tzinfo=UTC),
                "updated_at": datetime(2023, 1, 1, tzinfo=UTC),
                "completed_at": None,
                "deleted_at": None,
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "user_id": 1,
                "title": "Task 2",
                "description": "Description 2",
                "created_at": datetime(2023, 1, 2, tzinfo=UTC),
                "updated_at": datetime(2023, 1, 2, tzinfo=UTC),
                "completed_at": None,
                "deleted_at": None,
            },
        ]

    @pytest.fixture
    def mock_task_data(self):
        return {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "user_id": 1,
            "title": "Test Task",
            "description": "Test Description",
            "created_at": datetime(2023, 1, 1, tzinfo=UTC),
            "updated_at": datetime(2023, 1, 1, tzinfo=UTC),
            "completed_at": None,
            "deleted_at": None,
        }

    @pytest.fixture
    def task_update(self):
        return TaskUpdate(title="Updated Task", completed=True)

    @pytest.fixture
    def mock_updated_task(self):
        return {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "user_id": 1,
            "title": "Updated Task",
            "description": "Test Description",
            "created_at": datetime(2023, 1, 1, tzinfo=UTC),
            "updated_at": datetime(2023, 1, 2, tzinfo=UTC),
            "completed_at": datetime(2023, 1, 2, tzinfo=UTC),
            "deleted_at": None,
        }

    @pytest.fixture
    def mock_completed_task(self):
        return {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "user_id": 1,
            "title": "Test Task",
            "description": "Test Description",
            "created_at": datetime(2023, 1, 1, tzinfo=UTC),
            "updated_at": datetime(2023, 1, 2, tzinfo=UTC),
            "completed_at": datetime(2023, 1, 2, tzinfo=UTC),
            "deleted_at": None,
        }

    @pytest.fixture
    def mock_uncompleted_task(self):
        return {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "user_id": 1,
            "title": "Test Task",
            "description": "Test Description",
            "created_at": datetime(2023, 1, 1, tzinfo=UTC),
            "updated_at": datetime(2023, 1, 2, tzinfo=UTC),
            "completed_at": None,
            "deleted_at": None,
        }


class TestCreateTask(TestTaskBase):
    """Test cases for create_task endpoint"""

    @pytest.mark.asyncio
    async def test_create_task_success(self, mocker, mock_user, task_create, mock_now):
        # Arrange
        mock_collection = mocker.AsyncMock()
        mock_result = mocker.MagicMock()
        mock_result.inserted_id = ObjectId("507f1f77bcf86cd799439011")
        mock_collection.insert_one.return_value = mock_result

        mocker.patch(
            "app.routers.tasks.get_tasks_collection", return_value=mock_collection
        )

        # Act
        result = await create_task(task_create, mock_user)

        # Assert
        assert isinstance(result, TaskInDB)
        assert result.title == "Test Task"
        assert result.description == "Test Description"
        assert result.id == "507f1f77bcf86cd799439011"
        assert result.created_at == mock_now
        assert result.updated_at == mock_now
        assert result.completed_at is None

        # Verify collection was called with correct data
        mock_collection.insert_one.assert_called_once()
        call_args = mock_collection.insert_one.call_args[0][0]
        assert call_args["user_id"] == 1
        assert call_args["title"] == "Test Task"
        assert call_args["description"] == "Test Description"
        assert call_args["deleted_at"] is None
        assert call_args["completed_at"] is None


class TestListTasks(TestTaskBase):
    """Test cases for list_tasks endpoint"""

    @pytest.mark.asyncio
    async def test_list_tasks_success(self, mocker, mock_user, mock_tasks_data):
        # Arrange
        mock_collection = mocker.MagicMock()  # Changed from AsyncMock to MagicMock
        mock_cursor = mocker.AsyncMock()

        # Mock async iteration
        mock_cursor.__aiter__.return_value = iter(mock_tasks_data)

        # Mock the method chain: find().sort().skip().limit()
        mock_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = (
            mock_cursor
        )

        # Mock count_documents as async
        mock_collection.count_documents = mocker.AsyncMock(return_value=2)

        mocker.patch(
            "app.routers.tasks.get_tasks_collection", return_value=mock_collection
        )

        # Act
        result = await list_tasks(page=1, size=10, current_user=mock_user)

        # Assert
        assert isinstance(result, TaskList)
        assert len(result.tasks) == 2
        assert result.total == 2
        assert result.page == 1
        assert result.size == 10
        assert result.tasks[0].title == "Task 1"
        assert result.tasks[1].title == "Task 2"

        # Verify query parameters
        mock_collection.find.assert_called_once_with({"user_id": 1, "deleted_at": None})
        mock_collection.count_documents.assert_called_once_with(
            {"user_id": 1, "deleted_at": None}
        )

    @pytest.mark.asyncio
    async def test_list_tasks_with_pagination(self, mocker, mock_user, mock_tasks_data):
        # Arrange
        mock_collection = mocker.MagicMock()  # Changed from AsyncMock to MagicMock
        mock_cursor = mocker.AsyncMock()
        mock_cursor.__aiter__.return_value = iter(mock_tasks_data[:1])

        # Mock the method chain: find().sort().skip().limit()
        mock_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = (
            mock_cursor
        )

        # Mock count_documents as async
        mock_collection.count_documents = mocker.AsyncMock(return_value=5)

        mocker.patch(
            "app.routers.tasks.get_tasks_collection", return_value=mock_collection
        )

        # Act
        result = await list_tasks(page=2, size=1, current_user=mock_user)

        # Assert
        assert result.page == 2
        assert result.size == 1
        assert result.total == 5

        # Verify method calls in the chain
        mock_collection.find.assert_called_once_with({"user_id": 1, "deleted_at": None})
        mock_collection.find.return_value.sort.assert_called_once_with("created_at", -1)
        mock_collection.find.return_value.sort.return_value.skip.assert_called_once_with(
            1
        )
        mock_collection.find.return_value.sort.return_value.skip.return_value.limit.assert_called_once_with(
            1
        )


class TestGetTask(TestTaskBase):
    """Test cases for get_task endpoint"""

    @pytest.mark.asyncio
    async def test_get_task_success(self, mocker, mock_user, mock_task_data):
        # Arrange
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one.return_value = mock_task_data

        mocker.patch(
            "app.routers.tasks.get_tasks_collection", return_value=mock_collection
        )

        # Act
        result = await get_task("507f1f77bcf86cd799439011", mock_user)

        # Assert
        assert isinstance(result, TaskInDB)
        assert result.id == "507f1f77bcf86cd799439011"
        assert result.title == "Test Task"
        assert result.description == "Test Description"

        # Verify query
        mock_collection.find_one.assert_called_once_with(
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "user_id": 1,
                "deleted_at": None,
            }
        )

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, mocker, mock_user):
        # Arrange
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one.return_value = None

        mocker.patch(
            "app.routers.tasks.get_tasks_collection", return_value=mock_collection
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_task("507f1f77bcf86cd799439011", mock_user)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Task not found"


class TestUpdateTask(TestTaskBase):
    """Test cases for update_task endpoint"""

    @pytest.mark.asyncio
    async def test_update_task_success(
        self, mocker, mock_user, task_update, mock_updated_task, mock_now
    ):
        # Arrange
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one_and_update.return_value = mock_updated_task

        mocker.patch(
            "app.routers.tasks.get_tasks_collection", return_value=mock_collection
        )

        id = ObjectId("507f1f77bcf86cd799439011")
        # Act
        result = await update_task(task_update, id, mock_user)

        # Assert
        assert isinstance(result, TaskInDB)
        assert result.id == str(id)
        assert result.title == "Updated Task"

        # Verify update call
        mock_collection.find_one_and_update.assert_called_once()
        call_args = mock_collection.find_one_and_update.call_args

        # Check filter
        expected_filter = {"_id": id, "user_id": 1, "deleted_at": None}
        assert call_args[0][0] == expected_filter

        # Check update document
        update_doc = call_args[0][1]["$set"]
        assert update_doc["title"] == "Updated Task"
        assert update_doc["updated_at"] == mock_now
        assert update_doc["completed_at"] == mock_now
        assert "completed" not in update_doc  # Should be removed after processing

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, mocker, mock_user, task_update):
        # Arrange
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one_and_update.return_value = None

        mocker.patch(
            "app.routers.tasks.get_tasks_collection", return_value=mock_collection
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_task(
                task_update, ObjectId("507f1f77bcf86cd799439011"), mock_user
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Task not found"

    @pytest.mark.asyncio
    async def test_update_task_uncomplete(self, mocker, mock_user, mock_now):
        # Arrange
        task_update = TaskUpdate(completed=False)
        # Fix: Include all required fields for TaskInDB
        mock_updated_task = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "user_id": 1,
            "title": "Test Task",
            "description": "Test Description",  # Add missing description
            # Add missing created_at
            "created_at": datetime(2023, 1, 1, tzinfo=UTC),
            "completed_at": None,
            "updated_at": mock_now,
            "deleted_at": None,
        }

        mock_collection = mocker.AsyncMock()
        mock_collection.find_one_and_update.return_value = mock_updated_task

        mocker.patch(
            "app.routers.tasks.get_tasks_collection", return_value=mock_collection
        )

        # Act
        await update_task(task_update, ObjectId("507f1f77bcf86cd799439011"), mock_user)

        # Assert
        call_args = mock_collection.find_one_and_update.call_args[0][1]["$set"]
        assert call_args["completed_at"] is None


class TestDeleteTask(TestTaskBase):
    """Test cases for delete_task endpoint"""

    @pytest.mark.asyncio
    async def test_delete_task_success(self, mocker, mock_user, mock_now):
        # Arrange
        mock_collection = mocker.AsyncMock()
        mock_result = mocker.MagicMock()
        mock_result.matched_count = 1
        mock_collection.update_one.return_value = mock_result

        mocker.patch(
            "app.routers.tasks.get_tasks_collection", return_value=mock_collection
        )

        # Act
        result = await delete_task("507f1f77bcf86cd799439011", mock_user)

        # Assert
        assert result is None  # Should return None for 204 status

        # Verify soft delete
        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args

        expected_filter = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "user_id": 1,
            "deleted_at": None,
        }
        assert call_args[0][0] == expected_filter
        assert call_args[0][1]["$set"]["deleted_at"] == mock_now

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, mocker, mock_user):
        # Arrange
        mock_collection = mocker.AsyncMock()
        mock_result = mocker.MagicMock()
        mock_result.matched_count = 0
        mock_collection.update_one.return_value = mock_result

        mocker.patch(
            "app.routers.tasks.get_tasks_collection", return_value=mock_collection
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_task("507f1f77bcf86cd799439011", mock_user)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Task not found"


class TestMarkComplete(TestTaskBase):
    """Test cases for mark_complete endpoint"""

    @pytest.mark.asyncio
    async def test_mark_complete_success(self, mocker, mock_user, mock_now):
        # Fix: Use mock_now for completed_at to match what the function will set
        mock_completed_task = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "user_id": 1,
            "title": "Test Task",
            "description": "Test Description",
            "created_at": datetime(2023, 1, 1, tzinfo=UTC),
            "updated_at": mock_now,
            "completed_at": mock_now,  # Changed to use mock_now
            "deleted_at": None,
        }

        mock_collection = mocker.AsyncMock()
        mock_collection.find_one_and_update.return_value = mock_completed_task

        mocker.patch(
            "app.routers.tasks.get_tasks_collection", return_value=mock_collection
        )

        # Act
        result = await mark_complete("507f1f77bcf86cd799439011", mock_user)

        # Assert
        assert isinstance(result, TaskInDB)
        assert result.id == "507f1f77bcf86cd799439011"
        assert result.completed_at == mock_now

        # Verify update call
        mock_collection.find_one_and_update.assert_called_once()
        call_args = mock_collection.find_one_and_update.call_args

        expected_filter = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "user_id": 1,
            "deleted_at": None,
        }
        assert call_args[0][0] == expected_filter

        update_doc = call_args[0][1]["$set"]
        assert update_doc["completed_at"] == mock_now
        assert update_doc["updated_at"] == mock_now

    @pytest.mark.asyncio
    async def test_mark_complete_not_found(self, mocker, mock_user):
        # Arrange
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one_and_update.return_value = None

        mocker.patch(
            "app.routers.tasks.get_tasks_collection", return_value=mock_collection
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await mark_complete("507f1f77bcf86cd799439011", mock_user)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Task not found"


class TestMarkUncomplete(TestTaskBase):
    """Test cases for mark_uncomplete endpoint"""

    @pytest.mark.asyncio
    async def test_mark_uncomplete_success(
        self, mocker, mock_user, mock_uncompleted_task, mock_now
    ):
        # Arrange
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one_and_update.return_value = mock_uncompleted_task

        mocker.patch(
            "app.routers.tasks.get_tasks_collection", return_value=mock_collection
        )

        # Act
        result = await mark_uncomplete("507f1f77bcf86cd799439011", mock_user)

        # Assert
        assert isinstance(result, TaskInDB)
        assert result.id == "507f1f77bcf86cd799439011"
        assert result.completed_at is None

        # Verify update call
        mock_collection.find_one_and_update.assert_called_once()
        call_args = mock_collection.find_one_and_update.call_args

        expected_filter = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "user_id": 1,
            "deleted_at": None,
        }
        assert call_args[0][0] == expected_filter

        update_doc = call_args[0][1]["$set"]
        assert update_doc["completed_at"] is None
        assert update_doc["updated_at"] == mock_now

    @pytest.mark.asyncio
    async def test_mark_uncomplete_not_found(self, mocker, mock_user):
        # Arrange
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one_and_update.return_value = None

        mocker.patch(
            "app.routers.tasks.get_tasks_collection", return_value=mock_collection
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await mark_uncomplete("507f1f77bcf86cd799439011", mock_user)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Task not found"
