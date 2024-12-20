from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from typing import Dict, Any

from ...core.database.session import Base
from .user_model import User

class CommunityEvent(Base):
    """
    Community event model for organizing and managing voice-related events.
    """
    __tablename__ = 'community_events'

    id = Column(Integer, primary_key=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    
    # Event Details
    title = Column(String(200), nullable=False)
    description = Column(String(1000))
    event_type = Column(String(50), nullable=False)  # workshop, meetup, showcase
    
    # Organizer and Permissions
    organizer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_public = Column(Boolean, default=True)
    
    # Event Metadata
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    
    # Location and Connectivity
    location_type = Column(String(50), default='online')  # online, in-person, hybrid
    location_details = Column(JSON)
    
    # Participant Management
    max_participants = Column(Integer, default=50)
    registration_required = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organizer = relationship("User", back_populates="organized_events")
    participants = relationship(
        "EventParticipation", 
        back_populates="event", 
        cascade="all, delete-orphan"
    )

    def __init__(self, 
                 organizer_id: int, 
                 title: str, 
                 event_type: str, 
                 start_time: DateTime, 
                 end_time: DateTime, 
                 **kwargs):
        """
        Initialize a new community event.
        
        :param organizer_id: ID of the event organizer
        :param title: Event title
        :param event_type: Type of event
        :param start_time: Event start time
        :param end_time: Event end time
        :param kwargs: Additional event details
        """
        self.organizer_id = organizer_id
        self.title = title
        self.event_type = event_type
        self.start_time = start_time
        self.end_time = end_time
        
        # Set optional attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert community event to dictionary representation.
        
        :return: Dictionary of event details
        """
        return {
            'id': self.uuid,
            'title': self.title,
            'description': self.description,
            'event_type': self.event_type,
            'organizer': self.organizer.username,
            'is_public': self.is_public,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'location_type': self.location_type,
            'max_participants': self.max_participants,
            'registration_required': self.registration_required,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class EventParticipation(Base):
    """
    Model to track event participation and manage registrations.
    """
    __tablename__ = 'event_participations'

    id = Column(Integer, primary_key=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    
    # Participation Details
    event_id = Column(Integer, ForeignKey('community_events.id'), nullable=False)
    participant_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Participation Status
    status = Column(String(50), default='registered')  # registered, confirmed, cancelled
    
    # Additional Metadata
    registration_notes = Column(String(500))
    
    # Timestamps
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    event = relationship("CommunityEvent", back_populates="participants")
    participant = relationship("User", back_populates="event_participations")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event participation to dictionary representation.
        
        :return: Dictionary of participation details
        """
        return {
            'id': self.uuid,
            'event_id': self.event.uuid,
            'participant': self.participant.username,
            'status': self.status,
            'registered_at': self.registered_at.isoformat()
        }

# Add relationships to User model
User.organized_events = relationship(
    "CommunityEvent", 
    back_populates="organizer"
)
User.event_participations = relationship(
    "EventParticipation", 
    back_populates="participant"
)
