from datetime import datetime
from typing import List

import schemas
from main import app


@app.post("/meetings/", response_model=schemas.Meeting, status_code=201)
async def create_meeting(meeting: schemas.MeetingCreate):
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


@app.get("/meetings/", response_model=List[schemas.Meeting])
async def list_meetings():
    """
    List all meetings.
    """
    # Stub: Return empty list
    return []


@app.get("/meetings/{meeting_id}", response_model=schemas.MeetingWithDetails)
async def get_meeting(meeting_id: int):
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


@app.put("/meetings/{meeting_id}", response_model=schemas.Meeting)
async def update_meeting(meeting_id: int, meeting: schemas.MeetingUpdate):
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


@app.delete("/meetings/{meeting_id}", status_code=204)
async def delete_meeting(meeting_id: int):
    """
    Delete a meeting.
    """
    # Stub: Just return success
    return None
