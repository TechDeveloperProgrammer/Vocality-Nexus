from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import bcrypt
import uuid
from typing import Dict, Any

Base = declarative_base()

class User(Base):
    """
    User model representing registered users in Vocality Nexus.
    Supports diverse user identities and voice preferences.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Identity and Preference Fields
    display_name = Column(String(100))
    pronouns = Column(String(50))
    bio = Column(String(500))
    
    # Voice Profile Preferences
    voice_preferences = Column(JSON, default={
        'default_effect': 'neutral',
        'pitch_range': {'min': -2, 'max': 2},
        'preferred_gender_morph': None
    })
    
    # Community and Privacy Settings
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    privacy_settings = Column(JSON, default={
        'show_profile': True,
        'allow_dm': True,
        'discoverable': True
    })
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __init__(self, username: str, email: str, password: str):
        """
        Initialize a new user with hashed password.
        
        :param username: User's chosen username
        :param email: User's email address
        :param password: User's password (will be hashed)
        """
        self.username = username
        self.email = email
        self.password_hash = self._hash_password(password)

    def _hash_password(self, password: str) -> str:
        """
        Hash the user's password using bcrypt.
        
        :param password: Plain text password
        :return: Hashed password
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """
        Verify a given password against the stored hash.
        
        :param password: Plain text password to verify
        :return: True if password is correct, False otherwise
        """
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            self.password_hash.encode('utf-8')
        )

    def update_voice_preferences(self, preferences: Dict[str, Any]) -> None:
        """
        Update user's voice modulation preferences.
        
        :param preferences: Dictionary of voice preferences
        """
        current_prefs = self.voice_preferences or {}
        current_prefs.update(preferences)
        self.voice_preferences = current_prefs

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert user model to dictionary, excluding sensitive information.
        
        :return: User information dictionary
        """
        return {
            'id': self.uuid,
            'username': self.username,
            'display_name': self.display_name,
            'pronouns': self.pronouns,
            'bio': self.bio,
            'voice_preferences': self.voice_preferences,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def create_user(cls, username: str, email: str, password: str, **kwargs):
        """
        Class method to create a new user with additional optional parameters.
        
        :param username: User's username
        :param email: User's email
        :param password: User's password
        :param kwargs: Additional user attributes
        :return: New User instance
        """
        user = cls(username, email, password)
        
        # Set additional attributes
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        return user
