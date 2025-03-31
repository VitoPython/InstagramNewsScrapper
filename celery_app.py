from celery import Celery
from celery.schedules import crontab
import os

# Celery broker and backend settings
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    'instagram_scraper',
    broker=broker_url,
    backend=result_backend,
    include=['tasks']  # Include task modules
)

# Configure Celery settings
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Result settings
    result_expires=3600,  # 1 hour
    task_track_started=True,
    
    # Beat scheduler settings
    beat_schedule={
        'scrape-instagram-every-10-minutes': {
            'task': 'tasks.scrape_instagram_periodic',
            'schedule': crontab(minute='*/10'),  # Every 10 minutes
            'args': ['nasa', 10]  # username, num_posts
        }
    }
)

if __name__ == '__main__':
    celery_app.start() 