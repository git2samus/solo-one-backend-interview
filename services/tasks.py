from typing import List, Optional

import models
import schemas
from services.base import BaseService


class TaskService(BaseService):
    name = "tasks"

    def create(self, data: schemas.TaskCreate) -> schemas.Task:
        self.mesh.meetings.get(data.due_meeting_id)
        task = self._save(models.Task(**data.model_dump()))
        return schemas.Task.model_validate(task)

    def list(self, meeting_id: Optional[int] = None, status: Optional[str] = None) -> List[schemas.Task]:
        query = self.db.query(models.Task)
        if meeting_id is not None:
            query = query.filter(models.Task.due_meeting_id == meeting_id)
        if status is not None:
            query = query.filter(models.Task.status == status)
        return [schemas.Task.model_validate(task) for task in query.order_by(models.Task.id)]

    def get(self, task_id: int) -> schemas.Task:
        return schemas.Task.model_validate(self._get_model(models.Task, task_id))

    def update(self, task_id: int, data: schemas.TaskUpdate) -> schemas.Task:
        task = self._get_model(models.Task, task_id)
        changes = data.model_dump(exclude_unset=True)
        if changes.get("due_meeting_id") is not None:
            self.mesh.meetings.get(changes["due_meeting_id"])
        for field, value in changes.items():
            setattr(task, field, value)
        return schemas.Task.model_validate(self._save(task))

    def delete(self, task_id: int) -> None:
        task = self._get_model(models.Task, task_id)
        self.db.delete(task)
        self.db.commit()
