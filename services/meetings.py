from typing import List

import models
import schemas
from services.base import BaseService, ConflictError, NotFoundError


class MeetingService(BaseService):
    name = "meetings"

    def create(self, data: schemas.MeetingCreate) -> schemas.Meeting:
        meeting = models.Meeting(**data.model_dump(exclude={"attendee_ids"}))
        meeting.attendees = self._load_attendees(data.attendee_ids)
        return schemas.Meeting.model_validate(self._save(meeting))

    def list(self) -> List[schemas.Meeting]:
        meetings = self.db.query(models.Meeting).order_by(models.Meeting.id)
        return [schemas.Meeting.model_validate(meeting) for meeting in meetings]

    def get(self, meeting_id: int) -> schemas.MeetingWithDetails:
        return schemas.MeetingWithDetails.model_validate(self._get_model(models.Meeting, meeting_id))

    def update(self, meeting_id: int, data: schemas.MeetingUpdate) -> schemas.Meeting:
        meeting = self._get_model(models.Meeting, meeting_id)
        changes = data.model_dump(exclude_unset=True)
        attendee_ids = changes.pop("attendee_ids", None)
        for field, value in changes.items():
            setattr(meeting, field, value)
        if attendee_ids is not None:
            meeting.attendees = self._load_attendees(attendee_ids)
        return schemas.Meeting.model_validate(self._save(meeting))

    def delete(self, meeting_id: int) -> None:
        meeting = self._get_model(models.Meeting, meeting_id)
        if meeting.tasks:
            raise ConflictError(f"Meeting {meeting_id} has tasks due; reassign or delete them first")
        self.db.delete(meeting)
        self.db.commit()

    def _load_attendees(self, attendee_ids: List[int]) -> List[models.User]:
        if not attendee_ids:
            return []
        users = self.db.query(models.User).filter(models.User.id.in_(attendee_ids)).all()
        missing = set(attendee_ids) - {user.id for user in users}
        if missing:
            raise NotFoundError("User", min(missing))
        return users
