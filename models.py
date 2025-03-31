from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment variable or use SQLite as fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///instagram_posts.db")

# If PostgreSQL URL starts with postgres://, change it to postgresql://
# This is needed due to SQLAlchemy 1.4+ connection string changes
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create database engine
engine = create_engine(DATABASE_URL)

# Create declarative base
Base = declarative_base()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Post(Base):
    """Instagram post model"""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True)
    text = Column(Text)
    title = Column(String)
    likes = Column(String)
    comments = Column(String)
    hashtags = Column(Text)  # Stored as JSON string
    timestamp = Column(DateTime)
    username = Column(String, index=True)

# Create tables
Base.metadata.create_all(bind=engine) 