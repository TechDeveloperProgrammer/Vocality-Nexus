from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any

from ..models.user_model import User
from ..models.voice_profile_model import VoiceProfile

class VoiceProfileController:
    """
    Controller for managing voice profiles with advanced features.
    """
    
    def create_voice_profile(self, 
                              session: Session, 
                              user_uuid: str, 
                              name: str, 
                              voice_settings: Dict[str, Any], 
                              **kwargs) -> VoiceProfile:
        """
        Create a new voice profile for a user.
        
        :param session: Database session
        :param user_uuid: User's UUID
        :param name: Profile name
        :param voice_settings: Voice modulation settings
        :param kwargs: Additional optional parameters
        :return: Created VoiceProfile instance
        """
        # Find user by UUID
        user = session.query(User).filter_by(uuid=user_uuid).first()
        
        if not user:
            raise ValueError("User not found")
        
        # Create voice profile
        voice_profile = VoiceProfile(
            user_id=user.id, 
            name=name, 
            voice_settings=voice_settings,
            **kwargs
        )
        
        session.add(voice_profile)
        session.commit()
        session.refresh(voice_profile)
        
        return voice_profile
    
    def get_user_voice_profiles(self, 
                                 session: Session, 
                                 user_uuid: str) -> List[VoiceProfile]:
        """
        Retrieve all voice profiles for a specific user.
        
        :param session: Database session
        :param user_uuid: User's UUID
        :return: List of VoiceProfile instances
        """
        user = session.query(User).filter_by(uuid=user_uuid).first()
        
        if not user:
            raise ValueError("User not found")
        
        return user.voice_profiles
    
    def get_voice_profile(self, 
                           session: Session, 
                           user_uuid: str, 
                           profile_uuid: str) -> VoiceProfile:
        """
        Retrieve a specific voice profile for a user.
        
        :param session: Database session
        :param user_uuid: User's UUID
        :param profile_uuid: Voice profile UUID
        :return: VoiceProfile instance
        """
        user = session.query(User).filter_by(uuid=user_uuid).first()
        
        if not user:
            raise ValueError("User not found")
        
        profile = session.query(VoiceProfile).filter_by(
            uuid=profile_uuid, 
            user_id=user.id
        ).first()
        
        if not profile:
            raise ValueError("Voice profile not found")
        
        return profile
    
    def update_voice_profile(self, 
                              session: Session, 
                              user_uuid: str, 
                              profile_uuid: str, 
                              update_data: Dict[str, Any]) -> VoiceProfile:
        """
        Update a specific voice profile.
        
        :param session: Database session
        :param user_uuid: User's UUID
        :param profile_uuid: Voice profile UUID
        :param update_data: Dictionary of profile updates
        :return: Updated VoiceProfile instance
        """
        profile = self.get_voice_profile(session, user_uuid, profile_uuid)
        
        # Allowed update fields
        allowed_fields = [
            'name', 
            'description', 
            'voice_settings', 
            'is_public'
        ]
        
        for field, value in update_data.items():
            if field in allowed_fields:
                if field == 'voice_settings':
                    profile.update_settings(value)
                else:
                    setattr(profile, field, value)
        
        session.commit()
        session.refresh(profile)
        
        return profile
    
    def delete_voice_profile(self, 
                              session: Session, 
                              user_uuid: str, 
                              profile_uuid: str) -> None:
        """
        Delete a specific voice profile.
        
        :param session: Database session
        :param user_uuid: User's UUID
        :param profile_uuid: Voice profile UUID
        """
        profile = self.get_voice_profile(session, user_uuid, profile_uuid)
        
        session.delete(profile)
        session.commit()
    
    def get_community_profiles(self, 
                                session: Session, 
                                page: int = 1, 
                                per_page: int = 20) -> List[VoiceProfile]:
        """
        Retrieve public community voice profiles.
        
        :param session: Database session
        :param page: Page number for pagination
        :param per_page: Number of profiles per page
        :return: List of public VoiceProfile instances
        """
        offset = (page - 1) * per_page
        
        community_profiles = (
            session.query(VoiceProfile)
            .filter_by(is_public=True)
            .order_by(desc(VoiceProfile.is_featured), desc(VoiceProfile.created_at))
            .offset(offset)
            .limit(per_page)
            .all()
        )
        
        return community_profiles
