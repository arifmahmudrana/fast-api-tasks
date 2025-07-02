# tests/helpers/data_factories.py
import uuid
from typing import Dict, Optional


class TestDataFactory:
    @staticmethod
    def create_task_data(
        title_prefix: str = "Test Task", description: Optional[str] = None
    ) -> Dict[str, str]:
        """Create test task data with unique title"""
        return {
            "title": f"{title_prefix} {uuid.uuid4()}",
            "description": description or "Test task description",
        }

    @staticmethod
    def create_bulk_tasks(
        count: int, title_prefix: str = "Test Task"
    ) -> list[Dict[str, str]]:
        """Create multiple test tasks"""
        return [
            TestDataFactory.create_task_data(f"{title_prefix} {i+1}")
            for i in range(count)
        ]

    @staticmethod
    def create_task_update_data(
        title: Optional[str] = None, description: Optional[str] = None
    ) -> Dict[str, str]:
        """Create task update data with optional fields"""
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description
        return update_data
