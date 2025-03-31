from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine('sqlite:///instagram_posts.db')

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