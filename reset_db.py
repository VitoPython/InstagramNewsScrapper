"""
Database reset script
Creates a new database with empty tables
Run this script to reset the database
"""

from sqlalchemy import inspect
import os
import logging

from models import engine, Base, Post

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Reset the database by dropping all tables and recreating them"""
    
    logger.info("Starting database reset")
    
    # Check if database file exists and delete it
    if os.path.exists('instagram_posts.db'):
        logger.info("Removing existing database file")
        os.remove('instagram_posts.db')
    
    # Create all tables defined in models
    logger.info("Creating new database tables")
    Base.metadata.create_all(bind=engine)
    
    # Verify tables were created
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info(f"Created tables: {tables}")
    
    logger.info("Database reset complete")
    
if __name__ == "__main__":
    reset_database() 