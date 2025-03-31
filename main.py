from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from sqlalchemy.orm import Session
import uuid
import time
import os
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

from instagram_scraper import InstagramScraper
from models import SessionLocal, Post
from tasks import scrape_instagram, get_task_result
from celery_app import celery_app
from city_analyzer import CityAnalyzer
from news_fetcher import NewsFetcher

app = FastAPI(title="Instagram Scraper API")

# Create necessary directories if they don't exist
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Setup for static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Simulated Celery task storage (for backward compatibility)
celery_tasks = {}

# Initialize city analyzer and news fetcher
city_analyzer = CityAnalyzer()
news_fetcher = NewsFetcher()

# Setup logging
logger = logging.getLogger(__name__)

class PostBase(BaseModel):
    url: str
    text: str
    title: Optional[str] = ""
    likes: str
    comments: Optional[str] = "0"
    hashtags: List[str]
    timestamp: datetime
    username: str

    class Config:
        from_attributes = True

class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class NewsItem(BaseModel):
    title: str
    link: str
    published: str
    description: str
    full_text: str

class CityAnalysisResult(BaseModel):
    text: str
    cities: List[Dict[str, Any]]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Home page for news analysis
@app.get("/news/analyzer", response_class=HTMLResponse)
async def news_analyzer(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Instagram scraper endpoints
@app.post("/scrape/{username}", response_model=Dict[str, Any])
async def scrape_posts(username: str, num_posts: Optional[int] = 10, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    try:
        # Start Celery task
        celery_task = scrape_instagram.delay(username, num_posts)
        task_id = celery_task.id
        
        # Save task information for backward compatibility
        celery_tasks[task_id] = {
            "status": "STARTED",
            "created_at": datetime.now(),
            "completed_at": None,
            "result": None
        }
        
        # Return task ID
        return {
            "task_id": task_id,
            "status": "PROCESSING",
            "message": f"Task started to retrieve posts from {username}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape/manual/{username}", response_model=Dict[str, Any])
async def scrape_posts_manual(username: str, num_posts: Optional[int] = 10, db: Session = Depends(get_db)):
    """Manual start of the scraping task without Celery (for compatibility)"""
    try:
        # Create task ID
        task_id = str(uuid.uuid4())
        celery_tasks[task_id] = {
            "status": "STARTED",
            "created_at": datetime.now(),
            "completed_at": None,
            "result": None
        }
        
        # Create scraper instance and get posts
        scraper = InstagramScraper()
        posts = scraper.get_posts(username, num_posts)
        
        # Save posts to database
        saved_posts = []
        for post_data in posts:
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
            db.add(db_post)
            db.flush()  # Ensure ID is generated
            
            # Create new object for response with unchanged hashtags
            response_post = {
                "url": db_post.url,
                "text": db_post.text,
                "title": db_post.title,
                "likes": db_post.likes,
                "comments": db_post.comments,
                "hashtags": post_data["hashtags"],  # Use original hashtags
                "timestamp": db_post.timestamp,
                "username": db_post.username
            }
            saved_posts.append(response_post)
        
        db.commit()
        
        # Update task status
        celery_tasks[task_id]["status"] = "SUCCESS"
        celery_tasks[task_id]["completed_at"] = datetime.now()
        celery_tasks[task_id]["result"] = saved_posts
        
        # Return task ID and result
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "posts": saved_posts,
            "message": f"Successfully retrieved {len(saved_posts)} posts from {username}"
        }
        
    except Exception as e:
        # In case of error, also record it in the task storage
        if 'task_id' in locals():
            celery_tasks[task_id]["status"] = "FAILURE"
            celery_tasks[task_id]["completed_at"] = datetime.now()
            celery_tasks[task_id]["result"] = {"error": str(e)}
            
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/posts/{username}", response_model=List[PostBase])
async def get_posts(username: str, db: Session = Depends(get_db)):
    db_posts = db.query(Post).filter(Post.username == username).all()
    
    # Create list of objects for response
    result = []
    for post in db_posts:
        result.append({
            "url": post.url,
            "text": post.text,
            "title": post.title,
            "likes": post.likes,
            "comments": post.comments,
            "hashtags": json.loads(post.hashtags),  # Convert JSON string to list
            "timestamp": post.timestamp,
            "username": post.username
        })
    
    return result

@app.get("/posts/hashtag/{hashtag}", response_model=List[PostBase])
async def get_posts_by_hashtag(hashtag: str, db: Session = Depends(get_db)):
    # Add # at the beginning if it's missing
    if not hashtag.startswith('#'):
        hashtag = f"#{hashtag}"
    
    # Get all posts
    all_posts = db.query(Post).all()
    
    # Filter posts containing the specified hashtag
    result = []
    for post in all_posts:
        hashtags_list = json.loads(post.hashtags)
        if hashtag in hashtags_list:
            result.append({
                "url": post.url,
                "text": post.text,
                "title": post.title,
                "likes": post.likes,
                "comments": post.comments,
                "hashtags": hashtags_list,
                "timestamp": post.timestamp,
                "username": post.username
            })
    
    return result

@app.get("/posts/title/search", response_model=List[PostBase])
async def search_posts_by_title(query: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    # Get all posts containing the specified string in the title
    posts = db.query(Post).filter(Post.title.contains(query)).all()
    
    # Create list of objects for response
    result = []
    for post in posts:
        result.append({
            "url": post.url,
            "text": post.text,
            "title": post.title,
            "likes": post.likes,
            "comments": post.comments,
            "hashtags": json.loads(post.hashtags),  # Convert JSON string to list
            "timestamp": post.timestamp,
            "username": post.username
        })
    
    return result

@app.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task_status(task_id: str):
    # First check in Celery tasks
    celery_result = get_task_result(task_id)
    if celery_result:
        return {
            "task_id": task_id,
            "status": celery_result["status"],
            "result": celery_result["result"],
            "created_at": celery_result["created_at"],
            "completed_at": celery_result["completed_at"]
        }
    
    # Then check in local task storage
    if task_id in celery_tasks:
        task_info = celery_tasks[task_id]
        return {
            "task_id": task_id,
            "status": task_info["status"],
            "result": task_info["result"],
            "created_at": task_info["created_at"],
            "completed_at": task_info["completed_at"]
        }
    
    # If task not found
    raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

@app.get("/schedule")
async def get_schedule():
    """Get information about scheduled periodic tasks"""
    return {
        "scheduled_tasks": [
            {
                "name": "scrape-instagram-every-10-minutes",
                "task": "tasks.scrape_instagram_periodic",
                "schedule": "every 10 minutes",
                "args": ["nasa", 10]
            }
        ]
    }

# News analysis endpoints
@app.get("/news/sources")
async def get_news_sources():
    """Get list of available news sources"""
    return {"sources": list(news_fetcher.rss_feeds.keys())}

@app.get("/news/rss/{source}", response_model=List[NewsItem])
async def get_news(source: str = "bbc", limit: int = Query(5, ge=1, le=20)):
    """Get news from RSS feed"""
    news = news_fetcher.get_news_from_rss(source, limit)
    if not news:
        raise HTTPException(status_code=404, detail=f"Could not get news from source {source}")
    return news

@app.post("/news/analyze/city")
async def analyze_news_text(text: str = Form(...)):
    try:
        # Log for debugging
        logger.info(f"Received request to analyze text of length {len(text)} characters")
        
        # Analyze text
        cities = city_analyzer.extract_cities(text)
        
        # Log results
        logger.info(f"Found {len(cities)} cities in text")
        for city in cities:
            logger.info(f"City: {city['city']}, confidence: {city['confidence']}%")
        
        return {
            "text": text,
            "cities": cities
        }
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}")
        logger.exception("Detailed error information:")
        return {
            "text": text,
            "cities": [],
            "error": str(e)
        }

@app.get("/news/analyze/rss/{source}/{index}")
async def analyze_news_from_rss(source: str, index: int):
    try:
        # Get news from source
        news_items = news_fetcher.get_news_from_rss(source)
        
        if index < 0 or index >= len(news_items):
            return JSONResponse(status_code=404, content={"error": "News item not found"})
        
        # Get news text
        news = news_items[index]
        text = news.get("full_text", "")
        if not text:
            text = news.get("description", "")
        
        # Log for debugging
        logger.info(f"Analyzing news from RSS: {news['title']}")
        logger.info(f"Text for analysis: {text[:100]}... (length: {len(text)})")
        
        # Analyze text
        cities = city_analyzer.extract_cities(text)
        
        # Log results
        logger.info(f"Found {len(cities)} cities in news")
        for city in cities:
            logger.info(f"City: {city['city']}, confidence: {city['confidence']}%")
        
        return {
            "title": news["title"],
            "text": text,
            "cities": cities
        }
    except Exception as e:
        logger.error(f"Error analyzing news: {str(e)}")
        logger.exception("Detailed error information:")
        return {
            "text": "",
            "cities": [],
            "error": str(e)
        }

@app.get("/")
async def root(request: Request):
    """Main page with links to sections"""
    return templates.TemplateResponse("home.html", {
        "request": request,
        "links": [
            {"title": "Instagram Scraper API", "url": "/docs", "description": "API for Instagram scraping"},
            {"title": "City Analysis in News", "url": "/news/analyzer", "description": "Identify cities mentioned in news texts"}
        ]
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 