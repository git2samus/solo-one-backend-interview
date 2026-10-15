from typing import List

from sqlalchemy import delete, insert, or_, select
from sqlalchemy.orm import Query

import models
import schemas
from cache import cached
from services.base import BaseService, ConflictError, ForbiddenError, NotFoundError
from tools import expose_tools


@expose_tools
class MeetingService(BaseService):
    """
    A user can access meetings they own or attend; only the owner can delete.
    """

    name = "meetings"

    def create(self, data: schemas.MeetingCreate) -> schemas.Meeting:
        """
        Schedule a new meeting owned by the current user. attendee_ids lists the IDs of existing users to invite.
        """
        attendee_ids = self._check_attendees(data.attendee_ids)
        meeting = models.Meeting(**data.model_dump(exclude={"attendee_ids"}), owner_id=self.user_id)
        self.db.add(meeting)
        self.db.flush()
        self._set_attendees(meeting.id, attendee_ids)
        return schemas.Meeting.model_validate(self._save(meeting))

    @cached(reads=("users",))
    def list(self) -> List[schemas.Meeting]:
        """
        List the meetings the current user owns or attends, with their attendees.
        """
        meetings = self._accessible().order_by(models.Meeting.id)
        return [schemas.Meeting.model_validate(meeting) for meeting in meetings]

    @cached(reads=("users", "notes", "tasks"))
    def get(self, meeting_id: int) -> schemas.MeetingWithDetails:
        """
        Get a meeting the current user owns or attends, with its attendees, notes and tasks.
        """
        return schemas.MeetingWithDetails.model_validate(self._get_meeting(meeting_id))

    @cached
    def accessible_ids(self) -> List[int]:
        return [meeting_id for (meeting_id,) in self._accessible().with_entities(models.Meeting.id)]

    def update(self, meeting_id: int, data: schemas.MeetingUpdate) -> schemas.Meeting:
        """
        Update a meeting the current user owns or attends. Only the fields provided are changed; attendee_ids replaces the full attendee list.
        """
        meeting = self._get_meeting(meeting_id)
        changes = data.model_dump(exclude_unset=True)
        attendee_ids = changes.pop("attendee_ids", None)
        if attendee_ids is not None:
            attendee_ids = self._check_attendees(attendee_ids)
        for field, value in changes.items():
            setattr(meeting, field, value)
        if attendee_ids is not None:
            self._set_attendees(meeting.id, attendee_ids)
        return schemas.Meeting.model_validate(self._save(meeting))

    def delete(self, meeting_id: int) -> None:
        """
        Delete a meeting and its notes. Only the meeting's owner can delete it, and only once it has no tasks due.
        """
        meeting = self._get_meeting(meeting_id)
        if meeting.owner_id != self.user_id:
            raise ForbiddenError(f"Only the owner can delete meeting {meeting_id}")
        if meeting.tasks:
            raise ConflictError(f"Meeting {meeting_id} has tasks due; reassign or delete them first")
        self.db.delete(meeting)
        self.db.commit()

    def _accessible(self) -> Query:
        attending = select(models.meeting_users.c.meeting_id).where(
            models.meeting_users.c.user_id == self.user_id
        )
        return self.db.query(models.Meeting).filter(
            or_(models.Meeting.owner_id == self.user_id, models.Meeting.id.in_(attending))
        )

    def _get_meeting(self, meeting_id: int) -> models.Meeting:
        meeting = self._accessible().filter(models.Meeting.id == meeting_id).first()
        if meeting is None:
            raise NotFoundError("Meeting", meeting_id)
        return meeting

    def _check_attendees(self, attendee_ids: List[int]) -> List[int]:
        """
        Validate attendee ids through the users service; returns them de-duplicated.
        """
        attendee_ids = list(dict.fromkeys(attendee_ids))
        missing = self.mesh.users.missing_ids(attendee_ids) if attendee_ids else []
        if missing:
            raise NotFoundError("User", min(missing))
        return attendee_ids

    def _set_attendees(self, meeting_id: int, attendee_ids: List[int]) -> None:
        """
        Replace a meeting's attendees by writing the meeting_users association
        rows directly, so this service never reads the users table.
        """
        self.db.execute(delete(models.meeting_users).where(models.meeting_users.c.meeting_id == meeting_id))
        if attendee_ids:
            self.db.execute(
                insert(models.meeting_users),
                [{"meeting_id": meeting_id, "user_id": user_id} for user_id in attendee_ids],
            )
