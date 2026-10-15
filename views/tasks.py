from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Query

import schemas

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=schemas.Task, status_code=201)
async def create_task(task: schemas.TaskCreate):
    """
    Create a new task that is due at a specific meeting.
    """
    # Stub: Return a mock task
    return schemas.Task(
        id=1,
        title=task.title,
        description=task.description,
        status=task.status,
        due_meeting_id=task.due_meeting_id,
        created_at=datetime.utcnow()
    )


@router.get("/", response_model=List[schemas.Task])
async def list_tasks(meeting_id: Optional[int] = Query(None), status: Optional[str] = Query(None)):
    """
    List all tasks, optionally filtered by meeting_id or status.
    """
    # Stub: Return empty list
    return []


@router.get("/{task_id}", response_model=schemas.Task)
async def get_task(task_id: int):
    """
    Get a specific task by ID.
    """
    # Stub: Return a mock task
    return schemas.Task(
        id=task_id,
        title="Sample task",
        description="Sample task description",
        status="pending",
        due_meeting_id=1,
        created_at=datetime.utcnow()
    )


@router.put("/{task_id}", response_model=schemas.Task)
async def update_task(task_id: int, task: schemas.TaskUpdate):
    """
    Update a task (e.g., change status, reassign to different meeting).
    """
    # Stub: Return a mock updated task
    return schemas.Task(
        id=task_id,
        title=task.title or "Updated task",
        description=task.description,
        status=task.status or "pending",
        due_meeting_id=task.due_meeting_id or 1,
        created_at=datetime.utcnow()
    )


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int):
    """
    Delete a task.
    """
    # Stub: Just return success
    return None
