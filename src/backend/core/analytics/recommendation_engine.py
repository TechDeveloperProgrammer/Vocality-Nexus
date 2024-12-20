import numpy as np
import pandas as pd
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ...api.models.user_model import User
from ...api.models.voice_profile_model import VoiceProfile
from ...api.models.community_event_model import CommunityEvent

class RecommendationEngine:
    """
    Advanced recommendation system for Vocality Nexus.
    Provides personalized recommendations for events, voice profiles, and connections.
    """
    
    def __init__(self, session: Session):
        """
        Initialize recommendation engine.
        
        :param session: SQLAlchemy database session
        """
        self.session = session
        self.vectorizer = TfidfVectorizer(stop_words='english')
    
    def recommend_community_events(
        self, 
        user_uuid: str, 
        max_recommendations: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recommend community events based on user preferences.
        
        :param user_uuid: UUID of the user
        :param max_recommendations: Maximum number of recommendations
        :return: List of recommended events
        """
        user = self.session.query(User).filter_by(uuid=user_uuid).first()
        
        if not user:
            raise ValueError("User not found")
        
        # Extract user's interests and previous event participation
        user_interests = self._extract_user_interests(user)
        
        # Fetch all upcoming public events
        events = (
            self.session.query(CommunityEvent)
            .filter_by(is_public=True)
            .order_by(CommunityEvent.start_time)
            .limit(100)
            .all()
        )
        
        # Create event feature matrix
        event_features = self._create_event_feature_matrix(events)
        user_feature_vector = self._create_user_feature_vector(user_interests)
        
        # Compute similarity scores
        similarity_scores = cosine_similarity(
            user_feature_vector.reshape(1, -1), 
            event_features
        )[0]
        
        # Sort events by similarity
        recommended_event_indices = similarity_scores.argsort()[::-1][:max_recommendations]
        
        return [events[idx].to_dict() for idx in recommended_event_indices]
    
    def recommend_voice_profiles(
        self, 
        user_uuid: str, 
        max_recommendations: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recommend voice profiles based on user's voice characteristics.
        
        :param user_uuid: UUID of the user
        :param max_recommendations: Maximum number of recommendations
        :return: List of recommended voice profiles
        """
        user = self.session.query(User).filter_by(uuid=user_uuid).first()
        
        if not user:
            raise ValueError("User not found")
        
        # Fetch user's current voice profiles
        user_profiles = (
            self.session.query(VoiceProfile)
            .filter_by(user_id=user.id)
            .all()
        )
        
        # Fetch public community voice profiles
        community_profiles = (
            self.session.query(VoiceProfile)
            .filter_by(is_public=True)
            .limit(500)
            .all()
        )
        
        # Create feature matrices
        profile_features = self._create_voice_profile_feature_matrix(
            user_profiles + community_profiles
        )
        
        # Compute similarity scores
        similarity_scores = cosine_similarity(
            profile_features[:len(user_profiles)], 
            profile_features[len(user_profiles):]
        )
        
        # Average similarity across user's profiles
        avg_similarities = similarity_scores.mean(axis=0)
        recommended_profile_indices = avg_similarities.argsort()[::-1][:max_recommendations]
        
        return [community_profiles[idx].to_dict() for idx in recommended_profile_indices]
    
    def recommend_social_connections(
        self, 
        user_uuid: str, 
        max_recommendations: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recommend potential social connections.
        
        :param user_uuid: UUID of the user
        :param max_recommendations: Maximum number of recommendations
        :return: List of recommended users
        """
        user = self.session.query(User).filter_by(uuid=user_uuid).first()
        
        if not user:
            raise ValueError("User not found")
        
        # Extract user's interests and characteristics
        user_features = self._extract_user_features(user)
        
        # Fetch potential connection candidates
        potential_connections = (
            self.session.query(User)
            .filter(User.id != user.id)
            .limit(500)
            .all()
        )
        
        # Create feature matrix
        connection_features = self._create_connection_feature_matrix(potential_connections)
        user_feature_vector = self._create_user_feature_vector(user_features)
        
        # Compute similarity scores
        similarity_scores = cosine_similarity(
            user_feature_vector.reshape(1, -1), 
            connection_features
        )[0]
        
        # Sort potential connections by similarity
        recommended_connection_indices = similarity_scores.argsort()[::-1][:max_recommendations]
        
        return [potential_connections[idx].to_dict() for idx in recommended_connection_indices]
    
    def _extract_user_interests(self, user: User) -> Dict[str, Any]:
        """
        Extract user's interests and preferences.
        
        :param user: User model instance
        :return: Dictionary of user interests
        """
        return {
            'event_types': user.preferred_event_types or [],
            'voice_styles': user.preferred_voice_styles or [],
            'community_tags': user.community_tags or []
        }
    
    def _extract_user_features(self, user: User) -> Dict[str, Any]:
        """
        Extract comprehensive user features.
        
        :param user: User model instance
        :return: Dictionary of user features
        """
        return {
            'pronouns': user.pronouns,
            'interests': self._extract_user_interests(user),
            'voice_characteristics': user.voice_characteristics or {}
        }
    
    def _create_event_feature_matrix(self, events: List[CommunityEvent]) -> np.ndarray:
        """
        Create feature matrix for events.
        
        :param events: List of community events
        :return: Numpy array of event features
        """
        event_descriptions = [
            f"{event.title} {event.description} {event.event_type}"
            for event in events
        ]
        
        return self.vectorizer.fit_transform(event_descriptions).toarray()
    
    def _create_voice_profile_feature_matrix(self, profiles: List[VoiceProfile]) -> np.ndarray:
        """
        Create feature matrix for voice profiles.
        
        :param profiles: List of voice profiles
        :return: Numpy array of voice profile features
        """
        profile_descriptions = [
            f"{profile.name} {profile.description} {profile.voice_settings}"
            for profile in profiles
        ]
        
        return self.vectorizer.fit_transform(profile_descriptions).toarray()
    
    def _create_connection_feature_matrix(self, users: List[User]) -> np.ndarray:
        """
        Create feature matrix for potential connections.
        
        :param users: List of users
        :return: Numpy array of user features
        """
        user_descriptions = [
            f"{user.username} {user.display_name} {user.pronouns}"
            for user in users
        ]
        
        return self.vectorizer.fit_transform(user_descriptions).toarray()
    
    def _create_user_feature_vector(self, features: Dict[str, Any]) -> np.ndarray:
        """
        Convert user features to feature vector.
        
        :param features: Dictionary of user features
        :return: Numpy array of feature vector
        """
        feature_string = " ".join([
            str(features.get('pronouns', '')),
            " ".join(features.get('interests', {}).get('event_types', [])),
            " ".join(features.get('interests', {}).get('voice_styles', [])),
            " ".join(features.get('interests', {}).get('community_tags', []))
        ])
        
        return self.vectorizer.transform([feature_string]).toarray()[0]
