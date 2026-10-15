from typing import List, Optional

import models
import schemas
from cache import cached
from services.base import BaseService, NotFoundError


class NoteService(BaseService):
    """
    A user can access notes on meetings they can access.
    """

    name = "notes"

    def create(self, data: schemas.NoteCreate) -> schemas.Note:
        self.mesh.meetings.get(data.meeting_id)
        note = self._save(models.Note(**data.model_dump()))
        return schemas.Note.model_validate(note)

    @cached
    def list(self, meeting_id: Optional[int] = None) -> List[schemas.Note]:
        query = self.db.query(models.Note).filter(
            models.Note.meeting_id.in_(self.mesh.meetings.accessible_ids())
        )
        if meeting_id is not None:
            query = query.filter(models.Note.meeting_id == meeting_id)
        return [schemas.Note.model_validate(note) for note in query.order_by(models.Note.id)]

    @cached
    def get(self, note_id: int) -> schemas.Note:
        note = self.db.get(models.Note, note_id)
        if note is None or note.meeting_id not in self.mesh.meetings.accessible_ids():
            raise NotFoundError("Note", note_id)
        return schemas.Note.model_validate(note)
