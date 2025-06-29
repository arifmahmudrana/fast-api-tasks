from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from datetime import datetime, timezone
from bson import ObjectId
from app.schemas_task import TaskCreate, TaskUpdate, TaskInDB, TaskList
from app.mongo import tasks_collection
from fastapi import BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from app.deps import get_db

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Dummy user_id extraction for now (replace with real auth)


def get_current_user_id():
    return "demo-user-id"  # Replace with real user id from JWT


@router.post("/", response_model=TaskInDB, status_code=201)
async def create_task(task: TaskCreate):
    user_id = get_current_user_id()
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "title": task.title,
        "description": task.description,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
        "completed_at": None,
    }
    result = await tasks_collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return TaskInDB(**doc)


@router.get("/", response_model=TaskList)
async def list_tasks(page: int = 1, size: int = 10):
    user_id = get_current_user_id()
    skip = (page - 1) * size
    cursor = tasks_collection.find({"user_id": user_id, "deleted_at": None}).sort(
        "created_at", -1).skip(skip).limit(size)
    tasks = [TaskInDB(**{**doc, "_id": str(doc["_id"])}) async for doc in cursor]
    total = await tasks_collection.count_documents({"user_id": user_id, "deleted_at": None})
    return TaskList(tasks=tasks, total=total, page=page, size=size)


@router.get("/{task_id}", response_model=TaskInDB)
async def get_task(task_id: str):
    user_id = get_current_user_id()
    doc = await tasks_collection.find_one({"_id": ObjectId(task_id), "user_id": user_id, "deleted_at": None})
    if not doc:
        raise HTTPException(404, "Task not found")
    doc["_id"] = str(doc["_id"])
    return TaskInDB(**doc)


@router.put("/{task_id}", response_model=TaskInDB)
async def update_task(task_id: str, task: TaskUpdate):
    user_id = get_current_user_id()
    update = {k: v for k, v in task.dict(
        exclude_unset=True).items() if v is not None}
    update["updated_at"] = datetime.utcnow()
    if "completed" in update:
        update["completed_at"] = datetime.utcnow(
        ) if update.pop("completed") else None
    result = await tasks_collection.find_one_and_update(
        {"_id": ObjectId(task_id), "user_id": user_id, "deleted_at": None},
        {"$set": update},
        return_document=True
    )
    if not result:
        raise HTTPException(404, "Task not found")
    result["_id"] = str(result["_id"])
    return TaskInDB(**result)


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str):
    user_id = get_current_user_id()
    result = await tasks_collection.update_one(
        {"_id": ObjectId(task_id), "user_id": user_id, "deleted_at": None},
        {"$set": {"deleted_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Task not found")
    return


@router.post("/{task_id}/complete", response_model=TaskInDB)
async def mark_complete(task_id: str):
    user_id = get_current_user_id()
    now = datetime.utcnow()
    result = await tasks_collection.find_one_and_update(
        {"_id": ObjectId(task_id), "user_id": user_id, "deleted_at": None},
        {"$set": {"completed_at": now, "updated_at": now}},
        return_document=True
    )
    if not result:
        raise HTTPException(404, "Task not found")
    result["_id"] = str(result["_id"])
    return TaskInDB(**result)


@router.post("/{task_id}/uncomplete", response_model=TaskInDB)
async def mark_uncomplete(task_id: str):
    user_id = get_current_user_id()
    now = datetime.utcnow()
    result = await tasks_collection.find_one_and_update(
        {"_id": ObjectId(task_id), "user_id": user_id, "deleted_at": None},
        {"$set": {"completed_at": None, "updated_at": now}},
        return_document=True
    )
    if not result:
        raise HTTPException(404, "Task not found")
    result["_id"] = str(result["_id"])
    return TaskInDB(**result)
