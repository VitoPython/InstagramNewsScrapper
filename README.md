# Instagram Scraper API & News Analyzer

Multi-functional service for Instagram data collection and news analysis. The system includes:

1. **Instagram Scraper** - collects and stores data from public Instagram accounts
2. **News Analyzer** - analyses news texts from various sources, identifies cities mentioned in articles using Natural Language Processing (NLP)

## Features

### Instagram Scraper:
- Collection of posts from public Instagram accounts
- Background processing of data using Celery
- Storing results in a SQLite database
- API for accessing data with filtering by hashtags

### News Analyzer:
- Fetching news from various RSS sources
- Analysis of news texts using pre-trained NLP models
- City detection in news articles
- REST API for accessing analysis results
- Web interface for working with the analyzer

## Requirements
- Python 3.8+
- FastAPI
- SQLAlchemy
- Celery
- Redis
- Spacy (with English language model)
- BeautifulSoup4
- Feedparser

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/instagram-scraper-news-analyzer.git
cd instagram-scraper-news-analyzer
```

2. Install requirements:
```
pip install -r requirements.txt
```

3. Install Spacy language models:
```
python -m spacy download en_core_web_sm
```

4. Install and run Redis (required for Celery):
```
# For Linux
apt-get install redis-server
service redis-server start

# For macOS
brew install redis
brew services start redis

# For Windows
# Download and install from https://github.com/microsoftarchive/redis/releases
```

## Running the Application

### Running locally:

1. Start the FastAPI application:
```
python main.py
```

2. Start Celery worker (in a separate terminal):
```
python celery_worker.py
```

3. Start Celery beat scheduler (in a separate terminal, optional for periodic tasks):
```
python celery_beat.py
```

### Running with Docker:

```
docker-compose up -d
```

## API Endpoints

### Instagram Scraper:

- `POST /scrape/{username}` - Start scraping posts from an Instagram user
- `POST /scrape/manual/{username}` - Manual scraping without Celery
- `GET /posts/{username}` - Get posts for a specific username
- `GET /posts/hashtag/{hashtag}` - Get posts with a specific hashtag
- `GET /posts/title/search?query={query}` - Search posts by title
- `GET /tasks/{task_id}` - Get status of a scraping task
- `GET /schedule` - Get information about scheduled periodic tasks

### News Analyzer:

- `GET /news/sources` - Get list of available news sources
- `GET /news/rss/{source}` - Get news from specified RSS source
- `POST /news/analyze/city` - Analyze text to identify city mentions
- `GET /news/analyze/rss/{source}/{index}` - Analyze specific news article
- `GET /news/analyzer` - Web interface for news analysis
- `GET /` - Home page

## Project Structure

- `main.py` - FastAPI application and API endpoints
- `instagram_scraper.py` - Instagram scraping functionality
- `models.py` - Database models
- `tasks.py` - Celery tasks
- `celery_app.py` - Celery configuration
- `celery_worker.py` - Script to start Celery worker
- `celery_beat.py` - Script to start Celery beat scheduler
- `city_analyzer.py` - City detection in texts using NLP
- `news_fetcher.py` - RSS feed parsing and news retrieval
- `templates/` - HTML templates for web interface
- `static/` - Static files (CSS, JS)

## Notes

- The Instagram scraper uses simulated data as Instagram's terms of service prohibit scraping.
- For city analysis in news, a pre-trained BERT model is used.
- The system is designed for educational purposes.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 