from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(TaskBase):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


class TaskInDB(TaskBase):
    id: str = Field(..., alias="_id")
    user_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskList(BaseModel):
    tasks: List[TaskInDB]
    total: int
    page: int
    size: int
