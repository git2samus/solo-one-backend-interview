from typing import List, Optional

import models
import schemas
from services.base import BaseService


class NoteService(BaseService):
    name = "notes"

    def create(self, data: schemas.NoteCreate) -> schemas.Note:
        self.mesh.meetings.get(data.meeting_id)
        note = self._save(models.Note(**data.model_dump()))
        return schemas.Note.model_validate(note)

    def list(self, meeting_id: Optional[int] = None) -> List[schemas.Note]:
        query = self.db.query(models.Note)
        if meeting_id is not None:
            query = query.filter(models.Note.meeting_id == meeting_id)
        return [schemas.Note.model_validate(note) for note in query.order_by(models.Note.id)]

    def get(self, note_id: int) -> schemas.Note:
        return schemas.Note.model_validate(self._get_model(models.Note, note_id))
