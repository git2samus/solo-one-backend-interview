from typing import List, Optional

import models
import schemas
from cache import cached
from services.base import BaseService, NotFoundError
from tools import expose_tools


@expose_tools
class TaskService(BaseService):
    """
    A user can access tasks due at meetings they can access.
    """

    name = "tasks"

    def create(self, data: schemas.TaskCreate) -> schemas.Task:
        """
        Create a task due at a meeting the current user owns or attends. status is one of pending, completed or cancelled.
        """
        self.mesh.meetings.get(data.due_meeting_id)
        task = self._save(models.Task(**data.model_dump()))
        return schemas.Task.model_validate(task)

    @cached
    def list(self, meeting_id: Optional[int] = None, status: Optional[schemas.TaskStatus] = None) -> List[schemas.Task]:
        """
        List tasks due at meetings the current user owns or attends, optionally filtered by meeting and/or status.
        """
        query = self.db.query(models.Task).filter(
            models.Task.due_meeting_id.in_(self.mesh.meetings.accessible_ids())
        )
        if meeting_id is not None:
            query = query.filter(models.Task.due_meeting_id == meeting_id)
        if status is not None:
            query = query.filter(models.Task.status == status)
        return [schemas.Task.model_validate(task) for task in query.order_by(models.Task.id)]

    @cached
    def get(self, task_id: int) -> schemas.Task:
        """
        Get a task by ID, if it is due at a meeting the current user owns or attends.
        """
        return schemas.Task.model_validate(self._get_task(task_id))

    def update(self, task_id: int, data: schemas.TaskUpdate) -> schemas.Task:
        """
        Update a task, e.g. change its status or move it to another meeting the current user can access. Only the fields provided are changed.
        """
        task = self._get_task(task_id)
        changes = data.model_dump(exclude_unset=True)
        if changes.get("due_meeting_id") is not None:
            self.mesh.meetings.get(changes["due_meeting_id"])
        for field, value in changes.items():
            setattr(task, field, value)
        return schemas.Task.model_validate(self._save(task))

    def delete(self, task_id: int) -> None:
        """
        Delete a task.
        """
        self.db.delete(self._get_task(task_id))
        self.db.commit()

    def _get_task(self, task_id: int) -> models.Task:
        task = self.db.get(models.Task, task_id)
        if task is None or task.due_meeting_id not in self.mesh.meetings.accessible_ids():
            raise NotFoundError("Task", task_id)
        return task
