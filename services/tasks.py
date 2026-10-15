from typing import List, Optional

import models
import schemas
from cache import cached
from services.base import BaseService, NotFoundError


class TaskService(BaseService):
    """
    A user can access tasks due at meetings they can access.
    """

    name = "tasks"

    def create(self, data: schemas.TaskCreate) -> schemas.Task:
        self.mesh.meetings.get(data.due_meeting_id)
        task = self._save(models.Task(**data.model_dump()))
        return schemas.Task.model_validate(task)

    @cached
    def list(self, meeting_id: Optional[int] = None, status: Optional[str] = None) -> List[schemas.Task]:
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
        return schemas.Task.model_validate(self._get_task(task_id))

    def update(self, task_id: int, data: schemas.TaskUpdate) -> schemas.Task:
        task = self._get_task(task_id)
        changes = data.model_dump(exclude_unset=True)
        if changes.get("due_meeting_id") is not None:
            self.mesh.meetings.get(changes["due_meeting_id"])
        for field, value in changes.items():
            setattr(task, field, value)
        return schemas.Task.model_validate(self._save(task))

    def delete(self, task_id: int) -> None:
        self.db.delete(self._get_task(task_id))
        self.db.commit()

    def _get_task(self, task_id: int) -> models.Task:
        task = self.db.get(models.Task, task_id)
        if task is None or task.due_meeting_id not in self.mesh.meetings.accessible_ids():
            raise NotFoundError("Task", task_id)
        return task
