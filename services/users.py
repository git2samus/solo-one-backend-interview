from typing import List, Set

import models
import schemas
from services.base import BaseService, ConflictError, NotFoundError


class UserService(BaseService):
    """
    A user can see themselves and anyone they share a meeting with.
    """

    name = "users"

    def create(self, data: schemas.UserCreate) -> schemas.User:
        existing = self.db.query(models.User).filter(models.User.email == data.email).first()
        if existing is not None:
            raise ConflictError(f"User with email {data.email} already exists")
        user = self._save(models.User(**data.model_dump()))
        return schemas.User.model_validate(user)

    def list(self) -> List[schemas.User]:
        users = (
            self.db.query(models.User)
            .filter(models.User.id.in_(self._visible_ids()))
            .order_by(models.User.id)
        )
        return [schemas.User.model_validate(user) for user in users]

    def get(self, user_id: int) -> schemas.User:
        if user_id not in self._visible_ids():
            raise NotFoundError("User", user_id)
        return schemas.User.model_validate(self._get_model(models.User, user_id))

    def _visible_ids(self) -> Set[int]:
        visible = {self.user_id}
        for meeting in self.mesh.meetings.list():
            visible.add(meeting.owner_id)
            visible.update(attendee.id for attendee in meeting.attendees)
        return visible
