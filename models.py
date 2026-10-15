from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# Association table for many-to-many relationship between meetings and users
meeting_users = Table(
    'meeting_users',
    Base.metadata,
    Column('meeting_id', Integer, ForeignKey('meetings.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    
    # Relationships
    meetings = relationship('Meeting', secondary=meeting_users, back_populates='attendees')


class Meeting(Base):
    __tablename__ = 'meetings'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    scheduled_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    attendees = relationship('User', secondary=meeting_users, back_populates='meetings')
    notes = relationship('Note', back_populates='meeting', cascade='all, delete-orphan')
    tasks = relationship('Task', back_populates='due_meeting', foreign_keys='Task.due_meeting_id')


class Note(Base):
    __tablename__ = 'notes'
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    meeting_id = Column(Integer, ForeignKey('meetings.id'), nullable=False)
    
    # Relationships
    meeting = relationship('Meeting', back_populates='notes')


class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default='pending')  # pending, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    due_meeting_id = Column(Integer, ForeignKey('meetings.id'), nullable=False)
    
    # Relationships
    due_meeting = relationship('Meeting', back_populates='tasks', foreign_keys=[due_meeting_id])
