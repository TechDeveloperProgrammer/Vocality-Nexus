from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    'postgresql://postgres:postgres@localhost:5432/vocalitynexus'
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Test connections before using them
    pool_size=10,        # Number of connections in the pool
    max_overflow=20      # Maximum number of connections beyond pool_size
)

# Create a session factory
SessionLocal = sessionmaker(
    autocommit=False,     # Require explicit commits
    autoflush=False,      # Disable automatic flush
    bind=engine
)

# Create a scoped session for thread-local sessions
ScopedSession = scoped_session(SessionLocal)

# Base class for declarative models
Base = declarative_base()

def init_db():
    """
    Initialize the database by creating all tables defined in models.
    """
    from ...api.models import user_model  # Import models
    Base.metadata.create_all(bind=engine)

def drop_db():
    """
    Drop all tables in the database.
    Use with caution!
    """
    Base.metadata.drop_all(bind=engine)

def get_db():
    """
    Dependency that creates a new database session for each request.
    
    :yield: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
