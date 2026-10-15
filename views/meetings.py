from typing import List

from fastapi import APIRouter, Depends

import schemas
from mesh import ServiceMesh, get_mesh

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("/", response_model=schemas.Meeting, status_code=201)
def create_meeting(meeting: schemas.MeetingCreate, mesh: ServiceMesh = Depends(get_mesh)):
    """
    Create a new meeting with attendees.
    """
    return mesh.meetings.create(meeting)


@router.get("/", response_model=List[schemas.Meeting])
def list_meetings(mesh: ServiceMesh = Depends(get_mesh)):
    """
    List all meetings.
    """
    return mesh.meetings.list()


@router.get("/{meeting_id}", response_model=schemas.MeetingWithDetails)
def get_meeting(meeting_id: int, mesh: ServiceMesh = Depends(get_mesh)):
    """
    Get a specific meeting with all details (attendees, notes, tasks).
    """
    return mesh.meetings.get(meeting_id)


@router.put("/{meeting_id}", response_model=schemas.Meeting)
def update_meeting(meeting_id: int, meeting: schemas.MeetingUpdate, mesh: ServiceMesh = Depends(get_mesh)):
    """
    Update a meeting.
    """
    return mesh.meetings.update(meeting_id, meeting)


@router.delete("/{meeting_id}", status_code=204)
def delete_meeting(meeting_id: int, mesh: ServiceMesh = Depends(get_mesh)):
    """
    Delete a meeting.
    """
    mesh.meetings.delete(meeting_id)
