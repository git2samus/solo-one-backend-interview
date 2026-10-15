from __future__ import annotations
from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from typing import List, Literal, Optional


# User schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)


# Meeting schemas
class MeetingBase(BaseModel):
    title: str
    description: Optional[str] = None
    scheduled_time: datetime


class MeetingCreate(MeetingBase):
    attendee_ids: List[int] = []


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    attendee_ids: Optional[List[int]] = None


class Meeting(MeetingBase):
    id: int
    created_at: datetime
    owner_id: int
    attendees: List[User] = []
    
    model_config = ConfigDict(from_attributes=True)


# Note schemas
class NoteBase(BaseModel):
    content: str


class NoteCreate(NoteBase):
    meeting_id: int


class Note(NoteBase):
    id: int
    meeting_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Task schemas
TaskStatus = Literal['pending', 'completed', 'cancelled']


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = 'pending'


class TaskCreate(TaskBase):
    due_meeting_id: int


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_meeting_id: Optional[int] = None


class Task(TaskBase):
    id: int
    due_meeting_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# MeetingWithDetails must be defined after Note and Task
class MeetingWithDetails(Meeting):
    notes: List[Note] = []
    tasks: List[Task] = []
    
    model_config = ConfigDict(from_attributes=True)

