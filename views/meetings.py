from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends

import schemas
from middleware import get_current_user_id

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("/", response_model=schemas.Meeting, status_code=201)
async def create_meeting(meeting: schemas.MeetingCreate, current_user_id: int = Depends(get_current_user_id)):
    """
    Create a new meeting with attendees.
    """
    # Stub: Return a mock meeting
    return schemas.Meeting(
        id=1,
        title=meeting.title,
        description=meeting.description,
        scheduled_time=meeting.scheduled_time,
        created_at=meeting.scheduled_time,
        attendees=[]
    )


@router.get("/", response_model=List[schemas.Meeting])
async def list_meetings(current_user_id: int = Depends(get_current_user_id)):
    """
    List all meetings.
    """
    # Stub: Return empty list
    return []


@router.get("/{meeting_id}", response_model=schemas.MeetingWithDetails)
async def get_meeting(meeting_id: int, current_user_id: int = Depends(get_current_user_id)):
    """
    Get a specific meeting with all details (attendees, notes, tasks).
    """
    # Stub: Return a mock meeting with details
    return schemas.MeetingWithDetails(
        id=meeting_id,
        title="Team Standup",
        description="Daily standup meeting",
        scheduled_time=datetime.utcnow(),
        created_at=datetime.utcnow(),
        attendees=[],
        notes=[],
        tasks=[]
    )


@router.put("/{meeting_id}", response_model=schemas.Meeting)
async def update_meeting(meeting_id: int, meeting: schemas.MeetingUpdate, current_user_id: int = Depends(get_current_user_id)):
    """
    Update a meeting.
    """
    # Stub: Return a mock updated meeting
    return schemas.Meeting(
        id=meeting_id,
        title=meeting.title or "Updated Meeting",
        description=meeting.description,
        scheduled_time=meeting.scheduled_time or datetime.utcnow(),
        created_at=datetime.utcnow(),
        attendees=[]
    )


@router.delete("/{meeting_id}", status_code=204)
async def delete_meeting(meeting_id: int, current_user_id: int = Depends(get_current_user_id)):
    """
    Delete a meeting.
    """
    # Stub: Just return success
    return None
