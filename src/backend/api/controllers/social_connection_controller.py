from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Dict, Any

from ..models.user_model import User
from ..models.social_connection_model import SocialConnection, ConnectionStatus

class SocialConnectionController:
    """
    Controller for managing social connections and interactions.
    """
    
    def create_connection_request(self, 
                                  session: Session, 
                                  requester_uuid: str, 
                                  recipient_username: str, 
                                  connection_type: str = 'friend') -> SocialConnection:
        """
        Create a new connection request between users.
        
        :param session: Database session
        :param requester_uuid: UUID of the user sending the request
        :param recipient_username: Username of the user receiving the request
        :param connection_type: Type of social connection
        :return: Created SocialConnection instance
        """
        # Find requester and recipient
        requester = session.query(User).filter_by(uuid=requester_uuid).first()
        recipient = session.query(User).filter_by(username=recipient_username).first()
        
        if not requester or not recipient:
            raise ValueError("User not found")
        
        if requester.id == recipient.id:
            raise ValueError("Cannot create connection with yourself")
        
        # Check for existing connections
        existing_connection = (
            session.query(SocialConnection)
            .filter(
                or_(
                    (SocialConnection.requester_id == requester.id) & 
                    (SocialConnection.recipient_id == recipient.id),
                    (SocialConnection.requester_id == recipient.id) & 
                    (SocialConnection.recipient_id == requester.id)
                )
            )
            .first()
        )
        
        if existing_connection:
            raise ValueError("Connection already exists")
        
        # Create new connection
        connection = SocialConnection(
            requester_id=requester.id, 
            recipient_id=recipient.id,
            connection_type=connection_type
        )
        
        session.add(connection)
        session.commit()
        session.refresh(connection)
        
        return connection
    
    def update_connection_status(self, 
                                 session: Session, 
                                 recipient_uuid: str, 
                                 connection_uuid: str, 
                                 new_status: ConnectionStatus) -> SocialConnection:
        """
        Update the status of a social connection.
        
        :param session: Database session
        :param recipient_uuid: UUID of the user updating the connection
        :param connection_uuid: UUID of the connection
        :param new_status: New connection status
        :return: Updated SocialConnection instance
        """
        # Find recipient
        recipient = session.query(User).filter_by(uuid=recipient_uuid).first()
        
        if not recipient:
            raise ValueError("User not found")
        
        # Find connection
        connection = (
            session.query(SocialConnection)
            .filter_by(uuid=connection_uuid, recipient_id=recipient.id)
            .first()
        )
        
        if not connection:
            raise ValueError("Connection not found")
        
        # Update connection status
        connection.status = new_status
        
        session.commit()
        session.refresh(connection)
        
        return connection
    
    def get_user_connections(self, 
                              session: Session, 
                              user_uuid: str, 
                              status: ConnectionStatus = None) -> List[SocialConnection]:
        """
        Retrieve a user's social connections.
        
        :param session: Database session
        :param user_uuid: UUID of the user
        :param status: Optional status filter
        :return: List of SocialConnection instances
        """
        user = session.query(User).filter_by(uuid=user_uuid).first()
        
        if not user:
            raise ValueError("User not found")
        
        # Combine sent and received connections
        query = session.query(SocialConnection).filter(
            or_(
                SocialConnection.requester_id == user.id,
                SocialConnection.recipient_id == user.id
            )
        )
        
        if status:
            query = query.filter(SocialConnection.status == status)
        
        return query.all()
    
    def search_users(self, 
                     session: Session, 
                     search_query: str, 
                     current_user_uuid: str = None) -> List[Dict[str, Any]]:
        """
        Search for users based on username or display name.
        
        :param session: Database session
        :param search_query: Search term
        :param current_user_uuid: Optional UUID of current user to exclude
        :return: List of user dictionaries
        """
        query = session.query(User).filter(
            or_(
                User.username.ilike(f"%{search_query}%"),
                User.display_name.ilike(f"%{search_query}%")
            )
        )
        
        # Exclude current user if provided
        if current_user_uuid:
            current_user = session.query(User).filter_by(uuid=current_user_uuid).first()
            if current_user:
                query = query.filter(User.id != current_user.id)
        
        users = query.limit(50).all()
        
        return [
            {
                'username': user.username,
                'display_name': user.display_name,
                'pronouns': user.pronouns
            } for user in users
        ]
