from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from ...core.database.session import Base
from .user_model import User

class ConnectionStatus(enum.Enum):
    """
    Enum representing different states of social connections.
    """
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    BLOCKED = 'blocked'
    REJECTED = 'rejected'

class SocialConnection(Base):
    """
    Social connection model to manage user relationships and interactions.
    """
    __tablename__ = 'social_connections'

    id = Column(Integer, primary_key=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    
    # Connection participants
    requester_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    recipient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Connection status
    status = Column(Enum(ConnectionStatus), default=ConnectionStatus.PENDING)
    
    # Metadata
    connection_type = Column(String(50), default='friend')  # friend, follower, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    requester = relationship(
        "User", 
        foreign_keys=[requester_id], 
        back_populates="sent_connections"
    )
    recipient = relationship(
        "User", 
        foreign_keys=[recipient_id], 
        back_populates="received_connections"
    )

    def __init__(self, requester_id: int, recipient_id: int, connection_type: str = 'friend'):
        """
        Initialize a new social connection.
        
        :param requester_id: ID of the user initiating the connection
        :param recipient_id: ID of the user receiving the connection
        :param connection_type: Type of social connection
        """
        self.requester_id = requester_id
        self.recipient_id = recipient_id
        self.connection_type = connection_type
        self.status = ConnectionStatus.PENDING

    def to_dict(self):
        """
        Convert social connection to dictionary representation.
        
        :return: Dictionary of connection details
        """
        return {
            'id': self.uuid,
            'requester': self.requester.username,
            'recipient': self.recipient.username,
            'status': self.status.value,
            'connection_type': self.connection_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Add relationships to User model
User.sent_connections = relationship(
    "SocialConnection", 
    foreign_keys="[SocialConnection.requester_id]", 
    back_populates="requester"
)
User.received_connections = relationship(
    "SocialConnection", 
    foreign_keys="[SocialConnection.recipient_id]", 
    back_populates="recipient"
)
