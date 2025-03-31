# Instagram Scraper API & News Analyzer

Multi-functional service for Instagram data collection and news analysis. The system includes:

1. **Instagram Scraper** - collects and stores data from public Instagram accounts
2. **News Analyzer** - analyses news texts from various sources, identifies cities mentioned in articles using Natural Language Processing (NLP)

## Features

### Instagram Scraper:
- Collection of posts from public Instagram accounts
- Background processing of data using Celery
- Storing results in a database (SQLite locally, PostgreSQL in Docker)
- API for accessing data with filtering by hashtags

### News Analyzer:
- Fetching news from various RSS sources
- Analysis of news texts using pre-trained NLP models
- City detection in news articles
- REST API for accessing analysis results
- Web interface for working with the analyzer

## Requirements
- Python 3.9+
- FastAPI
- SQLAlchemy
- Celery
- Redis
- Spacy (with English language model)
- BeautifulSoup4
- Feedparser

## Installation

1. Clone the repository:
```bash
git clone https://github.com/VitoPython/InstagramNewsScrapper.git
cd InstagramNewsScrapper
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

3. Install Spacy language models:
```bash
python -m spacy download en_core_web_sm
```

4. Install and run Redis (required for Celery):
```bash
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
```bash
python main.py
```

2. Start Celery worker (in a separate terminal):
```bash
python celery_worker.py
```

3. Start Celery beat scheduler (in a separate terminal, optional for periodic tasks):
```bash
python celery_beat.py
```

### Running with Docker Compose (Recommended):

1. Make sure you have Docker and Docker Compose installed

2. Run the application stack:
```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- Redis for Celery broker
- FastAPI application on port 8000
- Celery worker for background tasks
- Celery beat for scheduled tasks

3. Access the application:
   - Web UI: http://localhost:8000/
   - API docs: http://localhost:8000/docs

4. Stop the application stack:
```bash
docker-compose down
```

### Docker Services

The application is divided into separate Docker containers:

1. **db** - PostgreSQL database for storing scraped data
2. **redis** - Redis server for Celery messaging
3. **api** - FastAPI application that handles HTTP requests
4. **worker** - Celery worker that processes background tasks
5. **beat** - Celery beat scheduler for recurring tasks

Each service can be scaled independently:

```bash
docker-compose up -d --scale worker=3
```

## CI/CD Pipeline

The project uses GitHub Actions for Continuous Integration and Deployment:

1. **Testing**: Runs unit tests and reports coverage
2. **Building**: Builds Docker images for each component
3. **Deployment**: Deploys the application to the target environment

### GitHub Actions Workflow

The CI/CD pipeline is defined in `.github/workflows/ci_cd.yml` and includes:

- Running tests with PostgreSQL and Redis services
- Building Docker images
- Pushing images to Docker Hub
- Deploying to the production environment

To set up CI/CD:

1. Add the following secrets to your GitHub repository:
   - `DOCKER_HUB_USERNAME` - Your Docker Hub username
   - `DOCKER_HUB_TOKEN` - Your Docker Hub access token

2. For deployment, configure additional secrets based on your hosting provider.

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
- `tests/` - Unit and integration tests
- `Dockerfile.api` - Docker configuration for API service
- `Dockerfile.worker` - Docker configuration for Celery worker
- `Dockerfile.beat` - Docker configuration for Celery beat
- `docker-compose.yml` - Docker Compose configuration
- `.github/workflows/` - CI/CD configuration

## Testing

Run the tests using pytest:

```bash
pytest
```

For code coverage:

```bash
pytest --cov=./ --cov-report=html
```

## Notes

- The Instagram scraper works with public Instagram accounts only
- For city analysis in news, a pre-trained NLP model is used
- The system is designed for educational purposes

## License

This project is licensed under the MIT License - see the LICENSE file for details. 