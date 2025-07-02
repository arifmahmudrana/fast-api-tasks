# app/routers/tasks.py
from datetime import UTC, datetime
from typing import Any, Dict

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

import app.deps as deps
import app.schemas as schemas
from app.mongo import get_tasks_collection
from app.schemas_task import TaskCreate, TaskInDB, TaskList, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])
get_task_id = Depends(deps.get_object_id_or_404("task_id", "Task ID"))


def convert_doc_to_task(doc: Dict[str, Any]) -> TaskInDB:
    """Convert MongoDB document to TaskInDB model"""
    doc_copy = doc.copy()
    doc_copy["_id"] = str(doc_copy["_id"])
    return TaskInDB(**doc_copy)


@router.post("/", response_model=TaskInDB, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate, current_user: schemas.User = Depends(deps.get_current_user)
):
    """Create a new task for the authenticated user"""
    now = datetime.now(UTC)
    doc = {
        "user_id": current_user.id,
        "title": task.title,
        "description": task.description,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
        "completed_at": None,
    }
    tasks_collection = get_tasks_collection()
    result = await tasks_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return convert_doc_to_task(doc)


@router.get("/", response_model=TaskList)
async def list_tasks(
    page: int = 1,
    size: int = 10,
    current_user: schemas.User = Depends(deps.get_current_user),
):
    """Get all tasks for the authenticated user"""
    user_id = current_user.id
    skip = (page - 1) * size
    tasks_collection = get_tasks_collection()
    cursor = (
        tasks_collection.find({"user_id": user_id, "deleted_at": None})
        .sort("created_at", -1)
        .skip(skip)
        .limit(size)
    )
    tasks = [convert_doc_to_task(doc) async for doc in cursor]
    total = await tasks_collection.count_documents(
        {"user_id": user_id, "deleted_at": None}
    )
    return TaskList(tasks=tasks, total=total, page=page, size=size)


@router.get("/{task_id}", response_model=TaskInDB)
async def get_task(
    task_id: ObjectId = get_task_id,
    current_user: schemas.User = Depends(deps.get_current_user),
):
    """Get a specific task for the authenticated user"""
    user_id = current_user.id
    tasks_collection = get_tasks_collection()
    doc = await tasks_collection.find_one(
        {"_id": ObjectId(task_id), "user_id": user_id, "deleted_at": None}
    )
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return convert_doc_to_task(doc)


@router.put("/{task_id}", response_model=TaskInDB)
async def update_task(
    task: TaskUpdate,
    task_id: ObjectId = get_task_id,
    current_user: schemas.User = Depends(deps.get_current_user),
):
    """Update a task for the authenticated user"""
    user_id = current_user.id
    update = {
        k: v for k, v in task.model_dump(exclude_unset=True).items() if v is not None
    }
    update["updated_at"] = datetime.now(UTC)
    if "completed" in update:
        update["completed_at"] = datetime.now(UTC) if update.pop("completed") else None
    tasks_collection = get_tasks_collection()
    result = await tasks_collection.find_one_and_update(
        {"_id": ObjectId(task_id), "user_id": user_id, "deleted_at": None},
        {"$set": update},
        return_document=True,
    )
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return convert_doc_to_task(result)


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: ObjectId = get_task_id,
    current_user: schemas.User = Depends(deps.get_current_user),
):
    """Delete a task for the authenticated user"""
    user_id = current_user.id
    tasks_collection = get_tasks_collection()
    result = await tasks_collection.update_one(
        {"_id": ObjectId(task_id), "user_id": user_id, "deleted_at": None},
        {"$set": {"deleted_at": datetime.now(UTC)}},
    )
    if result.matched_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return


@router.post("/{task_id}/complete", response_model=TaskInDB)
async def mark_complete(
    task_id: ObjectId = get_task_id,
    current_user: schemas.User = Depends(deps.get_current_user),
):
    """Mark a task as completed for the authenticated user"""
    user_id = current_user.id
    now = datetime.now(UTC)
    tasks_collection = get_tasks_collection()
    result = await tasks_collection.find_one_and_update(
        {"_id": ObjectId(task_id), "user_id": user_id, "deleted_at": None},
        {"$set": {"completed_at": now, "updated_at": now}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return convert_doc_to_task(result)


@router.post("/{task_id}/uncomplete", response_model=TaskInDB)
async def mark_uncomplete(
    task_id: ObjectId = get_task_id,
    current_user: schemas.User = Depends(deps.get_current_user),
):
    """Mark a task as uncompleted for the authenticated user"""
    user_id = current_user.id
    now = datetime.now(UTC)
    tasks_collection = get_tasks_collection()
    result = await tasks_collection.find_one_and_update(
        {"_id": ObjectId(task_id), "user_id": user_id, "deleted_at": None},
        {"$set": {"completed_at": None, "updated_at": now}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return convert_doc_to_task(result)
