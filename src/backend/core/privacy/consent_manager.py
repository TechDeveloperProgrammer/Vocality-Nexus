from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from typing import Dict, Any

from ...core.database.session import Base
from ..models.user_model import User

class UserConsent(Base):
    """
    Manage user consent for different data processing activities.
    """
    __tablename__ = 'user_consents'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Consent Flags
    voice_data_processing = Column(Boolean, default=False)
    analytics_tracking = Column(Boolean, default=False)
    marketing_communications = Column(Boolean, default=False)
    
    # Detailed Consent Metadata
    consent_details = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="consent")

    def __init__(self, user_id: int, **kwargs):
        """
        Initialize user consent record.
        
        :param user_id: ID of the user
        :param kwargs: Consent preferences
        """
        self.user_id = user_id
        
        # Set consent preferences
        self.voice_data_processing = kwargs.get('voice_data_processing', False)
        self.analytics_tracking = kwargs.get('analytics_tracking', False)
        self.marketing_communications = kwargs.get('marketing_communications', False)
        
        # Store detailed consent metadata
        self.consent_details = kwargs.get('consent_details', {})

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert consent record to dictionary.
        
        :return: Dictionary representation of consent
        """
        return {
            'voice_data_processing': self.voice_data_processing,
            'analytics_tracking': self.analytics_tracking,
            'marketing_communications': self.marketing_communications,
            'consent_details': self.consent_details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ConsentManager:
    """
    Service for managing user consent preferences.
    """
    
    @staticmethod
    def update_consent(session, user_uuid: str, consent_preferences: Dict[str, Any]) -> UserConsent:
        """
        Update user consent preferences.
        
        :param session: Database session
        :param user_uuid: User UUID
        :param consent_preferences: Updated consent preferences
        :return: Updated UserConsent instance
        """
        user = session.query(User).filter_by(uuid=user_uuid).first()
        
        if not user:
            raise ValueError("User not found")
        
        # Find or create consent record
        user_consent = user.consent if hasattr(user, 'consent') else UserConsent(user.id)
        
        # Update consent preferences
        for key, value in consent_preferences.items():
            if hasattr(user_consent, key):
                setattr(user_consent, key, value)
        
        user_consent.consent_details.update(consent_preferences.get('consent_details', {}))
        
        session.add(user_consent)
        session.commit()
        session.refresh(user_consent)
        
        return user_consent

# Add relationship to User model
User.consent = relationship(
    "UserConsent", 
    uselist=False, 
    back_populates="user"
)
