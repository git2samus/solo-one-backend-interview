from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

import schemas
from middleware import get_current_user_id

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=schemas.Note, status_code=201)
async def create_note(note: schemas.NoteCreate, current_user_id: int = Depends(get_current_user_id)):
    """
    Create a new note for a meeting.
    """
    # Stub: Return a mock note
    return schemas.Note(
        id=1,
        content=note.content,
        meeting_id=note.meeting_id,
        created_at=datetime.utcnow()
    )


@router.get("/", response_model=List[schemas.Note])
async def list_notes(meeting_id: Optional[int] = Query(None), current_user_id: int = Depends(get_current_user_id)):
    """
    List all notes, optionally filtered by meeting_id.
    """
    # Stub: Return empty list
    return []


@router.get("/{note_id}", response_model=schemas.Note)
async def get_note(note_id: int, current_user_id: int = Depends(get_current_user_id)):
    """
    Get a specific note by ID.
    """
    # Stub: Return a mock note
    return schemas.Note(
        id=note_id,
        content="Sample note content",
        meeting_id=1,
        created_at=datetime.utcnow()
    )
