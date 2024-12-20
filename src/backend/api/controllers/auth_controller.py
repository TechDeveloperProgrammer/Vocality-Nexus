from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any

from ..models.user_model import User
import re

class AuthController:
    """
    Controller for handling user authentication and profile management.
    """
    
    def validate_email(self, email: str) -> bool:
        """
        Validate email format.
        
        :param email: Email address to validate
        :return: True if email is valid, False otherwise
        """
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None
    
    def validate_password(self, password: str) -> bool:
        """
        Validate password strength.
        
        :param password: Password to validate
        :return: True if password meets requirements, False otherwise
        """
        # At least 8 characters, one uppercase, one lowercase, one number
        return (
            len(password) >= 8 and
            any(c.isupper() for c in password) and
            any(c.islower() for c in password) and
            any(c.isdigit() for c in password)
        )
    
    def register_user(self, 
                      session: Session, 
                      username: str, 
                      email: str, 
                      password: str, 
                      **kwargs) -> User:
        """
        Register a new user with validation.
        
        :param session: Database session
        :param username: User's username
        :param email: User's email
        :param password: User's password
        :param kwargs: Additional user attributes
        :return: Created User instance
        """
        # Validate inputs
        if not self.validate_email(email):
            raise ValueError("Invalid email format")
        
        if not self.validate_password(password):
            raise ValueError("Password does not meet complexity requirements")
        
        try:
            # Create user
            user = User.create_user(
                username=username, 
                email=email, 
                password=password, 
                **kwargs
            )
            
            session.add(user)
            session.commit()
            session.refresh(user)
            
            return user
        
        except IntegrityError:
            session.rollback()
            raise ValueError("Username or email already exists")
    
    def authenticate_user(self, 
                          session: Session, 
                          username: str, 
                          password: str) -> User:
        """
        Authenticate a user.
        
        :param session: Database session
        :param username: User's username
        :param password: User's password
        :return: Authenticated User instance
        """
        user = session.query(User).filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            raise ValueError("Invalid credentials")
        
        return user
    
    def get_user_by_uuid(self, session: Session, uuid: str) -> User:
        """
        Retrieve a user by their UUID.
        
        :param session: Database session
        :param uuid: User's UUID
        :return: User instance
        """
        user = session.query(User).filter_by(uuid=uuid).first()
        
        if not user:
            raise ValueError("User not found")
        
        return user
    
    def update_user_profile(self, 
                             session: Session, 
                             user_uuid: str, 
                             update_data: Dict[str, Any]) -> User:
        """
        Update user profile with validation.
        
        :param session: Database session
        :param user_uuid: User's UUID
        :param update_data: Dictionary of profile updates
        :return: Updated User instance
        """
        user = self.get_user_by_uuid(session, user_uuid)
        
        # Allowed update fields
        allowed_fields = [
            'display_name', 
            'pronouns', 
            'bio', 
            'voice_preferences', 
            'privacy_settings'
        ]
        
        for field, value in update_data.items():
            if field in allowed_fields:
                if field == 'voice_preferences':
                    user.update_voice_preferences(value)
                else:
                    setattr(user, field, value)
        
        session.commit()
        session.refresh(user)
        
        return user
