from typing import List

from sqlalchemy import or_
from sqlalchemy.orm import Query

import models
import schemas
from services.base import BaseService, ConflictError, ForbiddenError, NotFoundError


class MeetingService(BaseService):
    """
    A user can access meetings they own or attend; only the owner can delete.
    """

    name = "meetings"

    def create(self, data: schemas.MeetingCreate) -> schemas.Meeting:
        meeting = models.Meeting(**data.model_dump(exclude={"attendee_ids"}), owner_id=self.user_id)
        meeting.attendees = self._load_attendees(data.attendee_ids)
        return schemas.Meeting.model_validate(self._save(meeting))

    def list(self) -> List[schemas.Meeting]:
        meetings = self._accessible().order_by(models.Meeting.id)
        return [schemas.Meeting.model_validate(meeting) for meeting in meetings]

    def get(self, meeting_id: int) -> schemas.MeetingWithDetails:
        return schemas.MeetingWithDetails.model_validate(self._get_meeting(meeting_id))

    def accessible_ids(self) -> List[int]:
        return [meeting_id for (meeting_id,) in self._accessible().with_entities(models.Meeting.id)]

    def update(self, meeting_id: int, data: schemas.MeetingUpdate) -> schemas.Meeting:
        meeting = self._get_meeting(meeting_id)
        changes = data.model_dump(exclude_unset=True)
        attendee_ids = changes.pop("attendee_ids", None)
        for field, value in changes.items():
            setattr(meeting, field, value)
        if attendee_ids is not None:
            meeting.attendees = self._load_attendees(attendee_ids)
        return schemas.Meeting.model_validate(self._save(meeting))

    def delete(self, meeting_id: int) -> None:
        meeting = self._get_meeting(meeting_id)
        if meeting.owner_id != self.user_id:
            raise ForbiddenError(f"Only the owner can delete meeting {meeting_id}")
        if meeting.tasks:
            raise ConflictError(f"Meeting {meeting_id} has tasks due; reassign or delete them first")
        self.db.delete(meeting)
        self.db.commit()

    def _accessible(self) -> Query:
        return self.db.query(models.Meeting).filter(
            or_(
                models.Meeting.owner_id == self.user_id,
                models.Meeting.attendees.any(models.User.id == self.user_id),
            )
        )

    def _get_meeting(self, meeting_id: int) -> models.Meeting:
        meeting = self._accessible().filter(models.Meeting.id == meeting_id).first()
        if meeting is None:
            raise NotFoundError("Meeting", meeting_id)
        return meeting

    def _load_attendees(self, attendee_ids: List[int]) -> List[models.User]:
        if not attendee_ids:
            return []
        users = self.db.query(models.User).filter(models.User.id.in_(attendee_ids)).all()
        missing = set(attendee_ids) - {user.id for user in users}
        if missing:
            raise NotFoundError("User", min(missing))
        return users
