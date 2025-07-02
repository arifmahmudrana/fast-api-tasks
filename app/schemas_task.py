# app/schemas_task.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None


class TaskCreate(TaskBase):
    title: str = Field(..., min_length=1, description="Must not be empty")

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be empty")
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        # Only validate if title is not None
        if v is not None and not v.strip():
            raise ValueError("title must not be empty")
        return v


class TaskInDB(TaskBase):
    id: str = Field(..., alias="_id")
    user_id: int  # Add user_id field
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None  # Add deleted_at field

    model_config = {"populate_by_name": True}


class TaskList(BaseModel):
    tasks: List[TaskInDB]
    total: int
    page: int
    size: int
