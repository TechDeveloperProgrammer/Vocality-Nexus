from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Dict, Any
import uuid

from ...core.database.session import Base
from .user_model import User

class VoiceProfile(Base):
    """
    Voice Profile model representing a user's customized voice settings.
    Supports sharing and community features.
    """
    __tablename__ = 'voice_profiles'

    id = Column(Integer, primary_key=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Profile Metadata
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    
    # Voice Modulation Parameters
    voice_settings = Column(JSON, nullable=False, default={
        'pitch_shift': 0,
        'gender_morph': 'neutral',
        'effects': []
    })
    
    # Community and Sharing Settings
    is_public = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="voice_profiles")

    def __init__(self, user_id: int, name: str, voice_settings: Dict[str, Any], **kwargs):
        """
        Initialize a new voice profile.
        
        :param user_id: ID of the user creating the profile
        :param name: Name of the voice profile
        :param voice_settings: Dictionary of voice modulation settings
        :param kwargs: Additional optional parameters
        """
        self.user_id = user_id
        self.name = name
        self.voice_settings = voice_settings
        
        # Set optional attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert voice profile to dictionary representation.
        
        :return: Dictionary of voice profile details
        """
        return {
            'id': self.uuid,
            'name': self.name,
            'description': self.description,
            'voice_settings': self.voice_settings,
            'is_public': self.is_public,
            'is_featured': self.is_featured,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """
        Update voice profile settings.
        
        :param new_settings: Dictionary of new voice settings
        """
        current_settings = self.voice_settings or {}
        current_settings.update(new_settings)
        self.voice_settings = current_settings

# Add voice_profiles relationship to User model
User.voice_profiles = relationship(
    "VoiceProfile", 
    back_populates="user", 
    cascade="all, delete-orphan"
)
