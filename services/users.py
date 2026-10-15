from typing import List, Set

import models
import schemas
from cache import cached
from services.base import BaseService, ConflictError, NotFoundError
from tools import expose_tools


@expose_tools
class UserService(BaseService):
    """
    A user can see themselves and anyone they share a meeting with.
    """

    name = "users"

    def create(self, data: schemas.UserCreate) -> schemas.User:
        """
        Create a new user with a name and a unique email address.
        """
        existing = self.db.query(models.User).filter(models.User.email == data.email).first()
        if existing is not None:
            raise ConflictError(f"User with email {data.email} already exists")
        user = self._save(models.User(**data.model_dump()))
        return schemas.User.model_validate(user)

    @cached
    def list(self) -> List[schemas.User]:
        """
        List the current user and every user who shares a meeting with them (as owner or attendee).
        """
        users = (
            self.db.query(models.User)
            .filter(models.User.id.in_(self._visible_ids()))
            .order_by(models.User.id)
        )
        return [schemas.User.model_validate(user) for user in users]

    @cached
    def get(self, user_id: int) -> schemas.User:
        """
        Get a user by ID. Only the current user and users who share a meeting with them can be found.
        """
        if user_id not in self._visible_ids():
            raise NotFoundError("User", user_id)
        return schemas.User.model_validate(self._get_model(models.User, user_id))

    def _visible_ids(self) -> Set[int]:
        visible = {self.user_id}
        for meeting in self.mesh.meetings.list():
            visible.add(meeting.owner_id)
            visible.update(attendee.id for attendee in meeting.attendees)
        return visible
