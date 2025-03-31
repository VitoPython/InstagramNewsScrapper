from celery import shared_task
from datetime import datetime
import json
import time

from instagram_scraper import InstagramScraper
from models import SessionLocal, Post

@shared_task
def scrape_instagram(username, num_posts=10):
    """Celery task for Instagram scraping"""
    try:
        # Create scraper instance
        scraper = InstagramScraper()
        
        # Get posts
        posts = scraper.get_posts(username, num_posts)
        
        # Save posts to database
        db = SessionLocal()
        
        saved_posts = []
        for post_data in posts:
            # Create database record
            db_post = Post(
                url=post_data["url"],
                text=post_data["text"],
                title=post_data.get("title", ""),
                likes=post_data["likes"],
                comments=post_data.get("comments", "0"),
                hashtags=json.dumps(post_data["hashtags"]),
                timestamp=datetime.fromisoformat(post_data["timestamp"]),
                username=username
            )
            
            # Add to session
            db.add(db_post)
            db.flush()  # To get ID before commit
            
            # Create new object for response with unchanged hashtags
            response_post = {
                "id": db_post.id,
                "url": db_post.url,
                "text": db_post.text,
                "title": db_post.title,
                "likes": db_post.likes,
                "comments": db_post.comments,
                "hashtags": post_data["hashtags"],  # Use original hashtags
                "timestamp": post_data["timestamp"],
                "username": db_post.username
            }
            saved_posts.append(response_post)
        
        # Commit changes to database
        db.commit()
        
        # Close connection
        db.close()
        
        # Return result
        return {
            "status": "SUCCESS",
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "result": saved_posts
        }
        
    except Exception as e:
        return {
            "status": "FAILURE",
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "result": {"error": str(e)}
        }

@shared_task
def scrape_instagram_periodic(username="nasa", num_posts=10):
    """Periodic task for Instagram scraping"""
    return scrape_instagram(username, num_posts)

def get_task_result(task_id):
    """Get Celery task result"""
    from celery_app import celery_app
    
    try:
        result = celery_app.AsyncResult(task_id)
        
        if result.ready():
            return {
                "status": "SUCCESS" if result.successful() else "FAILURE",
                "created_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "result": result.result
            }
        else:
            return {
                "status": "PROCESSING",
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
                "result": None
            }
    except Exception as e:
        return {
            "status": "ERROR",
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "result": {"error": str(e)}
        } 