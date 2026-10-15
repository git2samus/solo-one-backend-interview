from typing import List, Optional

from fastapi import APIRouter, Depends, Query

import schemas
from mesh import ServiceMesh, get_mesh

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=schemas.Note, status_code=201)
def create_note(note: schemas.NoteCreate, mesh: ServiceMesh = Depends(get_mesh)):
    """
    Create a new note for a meeting.
    """
    return mesh.notes.create(note)


@router.get("/", response_model=List[schemas.Note])
def list_notes(meeting_id: Optional[int] = Query(None), mesh: ServiceMesh = Depends(get_mesh)):
    """
    List all notes, optionally filtered by meeting_id.
    """
    return mesh.notes.list(meeting_id=meeting_id)


@router.get("/{note_id}", response_model=schemas.Note)
def get_note(note_id: int, mesh: ServiceMesh = Depends(get_mesh)):
    """
    Get a specific note by ID.
    """
    return mesh.notes.get(note_id)
