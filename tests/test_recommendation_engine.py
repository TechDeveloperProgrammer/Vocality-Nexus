import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.backend.core.analytics.recommendation_engine import RecommendationEngine
from src.backend.api.models.user_model import User
from src.backend.api.models.voice_profile_model import VoiceProfile
from src.backend.api.models.community_event_model import CommunityEvent

@pytest.fixture(scope='module')
def test_engine():
    """
    Create a test database engine.
    """
    return create_engine('sqlite:///:memory:')

@pytest.fixture(scope='module')
def TestSession(test_engine):
    """
    Create a test session factory.
    """
    # Create tables
    User.metadata.create_all(test_engine)
    VoiceProfile.metadata.create_all(test_engine)
    CommunityEvent.metadata.create_all(test_engine)
    
    # Create session
    return sessionmaker(bind=test_engine)

@pytest.fixture
def session(TestSession):
    """
    Create a new session for each test.
    """
    session = TestSession()
    yield session
    session.close()

@pytest.fixture
def recommendation_engine(session):
    """
    Create a recommendation engine for testing.
    """
    return RecommendationEngine(session)

def test_recommendation_engine_initialization(recommendation_engine):
    """
    Test that the recommendation engine is initialized correctly.
    """
    assert recommendation_engine is not None
    assert hasattr(recommendation_engine, 'session')
    assert hasattr(recommendation_engine, 'vectorizer')

def test_recommend_community_events(session, recommendation_engine):
    """
    Test community event recommendations.
    """
    # Create a test user
    user = User(
        username='test_user',
        email='test@example.com',
        preferred_event_types=['music', 'tech'],
        community_tags=['ai', 'voice']
    )
    session.add(user)
    session.commit()
    
    # Create some test events
    events = [
        CommunityEvent(
            title='AI Music Workshop',
            description='Workshop on AI and music technology',
            event_type='tech',
            is_public=True
        ),
        CommunityEvent(
            title='Voice Tech Conference',
            description='Conference on voice technologies',
            event_type='tech',
            is_public=True
        )
    ]
    session.add_all(events)
    session.commit()
    
    # Get recommendations
    recommendations = recommendation_engine.recommend_community_events(
        user.uuid, 
        max_recommendations=2
    )
    
    assert len(recommendations) > 0
    assert all('title' in event for event in recommendations)

def test_recommend_voice_profiles(session, recommendation_engine):
    """
    Test voice profile recommendations.
    """
    # Create a test user
    user = User(
        username='test_user',
        email='test@example.com',
        preferred_voice_styles=['warm', 'deep']
    )
    session.add(user)
    session.commit()
    
    # Create some test voice profiles
    profiles = [
        VoiceProfile(
            name='Deep Voice Profile',
            description='A deep, warm voice profile',
            voice_settings='{"timbre": "warm", "pitch": "low"}',
            is_public=True,
            user_id=user.id
        ),
        VoiceProfile(
            name='Tech Voice Profile',
            description='A crisp, clear tech-oriented voice',
            voice_settings='{"timbre": "bright", "pitch": "medium"}',
            is_public=True
        )
    ]
    session.add_all(profiles)
    session.commit()
    
    # Get recommendations
    recommendations = recommendation_engine.recommend_voice_profiles(
        user.uuid, 
        max_recommendations=2
    )
    
    assert len(recommendations) > 0
    assert all('name' in profile for profile in recommendations)

def test_recommend_social_connections(session, recommendation_engine):
    """
    Test social connection recommendations.
    """
    # Create test users
    users = [
        User(
            username='user1',
            email='user1@example.com',
            pronouns='he/him',
            community_tags=['ai', 'voice']
        ),
        User(
            username='user2',
            email='user2@example.com',
            pronouns='she/her',
            community_tags=['music', 'tech']
        )
    ]
    session.add_all(users)
    session.commit()
    
    # Get recommendations for first user
    recommendations = recommendation_engine.recommend_social_connections(
        users[0].uuid, 
        max_recommendations=2
    )
    
    assert len(recommendations) > 0
    assert all('username' in user for user in recommendations)

def test_edge_cases_and_error_handling(session, recommendation_engine):
    """
    Test edge cases and error handling in recommendation engine.
    """
    # Test with non-existent user
    with pytest.raises(ValueError):
        recommendation_engine.recommend_community_events(
            'non_existent_uuid', 
            max_recommendations=2
        )
    
    # Test with zero max recommendations
    recommendations = recommendation_engine.recommend_community_events(
        session.query(User).first().uuid, 
        max_recommendations=0
    )
    assert len(recommendations) == 0

def test_recommendation_diversity(session, recommendation_engine):
    """
    Test that recommendations have some diversity.
    """
    # Create a diverse set of events and profiles
    events = [
        CommunityEvent(title='AI Workshop', event_type='tech', is_public=True),
        CommunityEvent(title='Music Hackathon', event_type='music', is_public=True),
        CommunityEvent(title='Voice Tech Conference', event_type='tech', is_public=True)
    ]
    session.add_all(events)
    session.commit()
    
    user = session.query(User).first()
    
    recommendations = recommendation_engine.recommend_community_events(
        user.uuid, 
        max_recommendations=3
    )
    
    # Check that recommendations are not all the same
    event_types = [event['event_type'] for event in recommendations]
    assert len(set(event_types)) > 1  # Should have more than one event type
