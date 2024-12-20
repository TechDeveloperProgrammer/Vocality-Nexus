from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List, Dict, Any

from ..models.user_model import User
from ..models.community_event_model import CommunityEvent, EventParticipation

class CommunityEventController:
    """
    Controller for managing community events and event participation.
    """
    
    def create_event(self, 
                     session: Session, 
                     organizer_uuid: str, 
                     title: str, 
                     event_type: str, 
                     start_time: datetime, 
                     end_time: datetime, 
                     **kwargs) -> CommunityEvent:
        """
        Create a new community event.
        
        :param session: Database session
        :param organizer_uuid: UUID of the event organizer
        :param title: Event title
        :param event_type: Type of event
        :param start_time: Event start time
        :param end_time: Event end time
        :param kwargs: Additional event details
        :return: Created CommunityEvent instance
        """
        # Find organizer
        organizer = session.query(User).filter_by(uuid=organizer_uuid).first()
        
        if not organizer:
            raise ValueError("Organizer not found")
        
        if start_time >= end_time:
            raise ValueError("End time must be after start time")
        
        # Create event
        event = CommunityEvent(
            organizer_id=organizer.id, 
            title=title,
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            **kwargs
        )
        
        session.add(event)
        session.commit()
        session.refresh(event)
        
        return event
    
    def register_for_event(self, 
                           session: Session, 
                           event_uuid: str, 
                           participant_uuid: str, 
                           registration_notes: str = None) -> EventParticipation:
        """
        Register a user for a community event.
        
        :param session: Database session
        :param event_uuid: UUID of the event
        :param participant_uuid: UUID of the participant
        :param registration_notes: Optional registration notes
        :return: Created EventParticipation instance
        """
        # Find event and participant
        event = session.query(CommunityEvent).filter_by(uuid=event_uuid).first()
        participant = session.query(User).filter_by(uuid=participant_uuid).first()
        
        if not event or not participant:
            raise ValueError("Event or participant not found")
        
        # Check event capacity
        current_participants = (
            session.query(func.count(EventParticipation.id))
            .filter_by(event_id=event.id)
            .scalar()
        )
        
        if current_participants >= event.max_participants:
            raise ValueError("Event is at full capacity")
        
        # Check for existing registration
        existing_registration = (
            session.query(EventParticipation)
            .filter_by(event_id=event.id, participant_id=participant.id)
            .first()
        )
        
        if existing_registration:
            raise ValueError("Already registered for this event")
        
        # Create registration
        registration = EventParticipation(
            event_id=event.id,
            participant_id=participant.id,
            registration_notes=registration_notes
        )
        
        session.add(registration)
        session.commit()
        session.refresh(registration)
        
        return registration
    
    def get_events(self, 
                   session: Session, 
                   page: int = 1, 
                   per_page: int = 20, 
                   filters: Dict[str, Any] = None) -> List[CommunityEvent]:
        """
        Retrieve community events with optional filtering.
        
        :param session: Database session
        :param page: Page number for pagination
        :param per_page: Number of events per page
        :param filters: Optional dictionary of filter parameters
        :return: List of CommunityEvent instances
        """
        query = session.query(CommunityEvent)
        
        # Apply filters
        if filters:
            if 'event_type' in filters:
                query = query.filter(CommunityEvent.event_type == filters['event_type'])
            
            if 'is_public' in filters:
                query = query.filter(CommunityEvent.is_public == filters['is_public'])
            
            if 'start_after' in filters:
                query = query.filter(CommunityEvent.start_time >= filters['start_after'])
            
            if 'end_before' in filters:
                query = query.filter(CommunityEvent.end_time <= filters['end_before'])
        
        # Order by start time
        query = query.order_by(CommunityEvent.start_time)
        
        # Pagination
        offset = (page - 1) * per_page
        events = query.offset(offset).limit(per_page).all()
        
        return events
    
    def get_event_participants(self, 
                               session: Session, 
                               event_uuid: str) -> List[Dict[str, Any]]:
        """
        Retrieve participants for a specific event.
        
        :param session: Database session
        :param event_uuid: UUID of the event
        :return: List of participant details
        """
        event = session.query(CommunityEvent).filter_by(uuid=event_uuid).first()
        
        if not event:
            raise ValueError("Event not found")
        
        participants = (
            session.query(User)
            .join(EventParticipation)
            .filter(EventParticipation.event_id == event.id)
            .all()
        )
        
        return [
            {
                'username': participant.username,
                'display_name': participant.display_name,
                'pronouns': participant.pronouns
            } for participant in participants
        ]
