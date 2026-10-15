from typing import List, Optional

from fastapi import APIRouter, Depends, Query

import schemas
from mesh import ServiceMesh, get_mesh

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=schemas.Task, status_code=201)
def create_task(task: schemas.TaskCreate, mesh: ServiceMesh = Depends(get_mesh)):
    """
    Create a new task that is due at a specific meeting.
    """
    return mesh.tasks.create(task)


@router.get("/", response_model=List[schemas.Task])
def list_tasks(
    meeting_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    mesh: ServiceMesh = Depends(get_mesh),
):
    """
    List all tasks, optionally filtered by meeting_id or status.
    """
    return mesh.tasks.list(meeting_id=meeting_id, status=status)


@router.get("/{task_id}", response_model=schemas.Task)
def get_task(task_id: int, mesh: ServiceMesh = Depends(get_mesh)):
    """
    Get a specific task by ID.
    """
    return mesh.tasks.get(task_id)


@router.put("/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, task: schemas.TaskUpdate, mesh: ServiceMesh = Depends(get_mesh)):
    """
    Update a task (e.g., change status, reassign to different meeting).
    """
    return mesh.tasks.update(task_id, task)


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, mesh: ServiceMesh = Depends(get_mesh)):
    """
    Delete a task.
    """
    mesh.tasks.delete(task_id)
