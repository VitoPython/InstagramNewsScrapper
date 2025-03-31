import feedparser
import requests
from bs4 import BeautifulSoup
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsFetcher:
    """Class for retrieving news from RSS feeds of various sources"""
    
    def __init__(self):
        """Initialize the class with RSS feed settings"""
        # Dictionary with URLs of RSS feeds from various news sources
        self.rss_feeds = {
            "bbc": "https://feeds.bbci.co.uk/news/world/rss.xml",
            "cnn": "http://rss.cnn.com/rss/edition_world.rss",
            # Removed Reuters due to authorization issues
            "nytimes": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
            "guardian": "https://www.theguardian.com/world/rss",
            "ap": "https://apnews.com/hub/world-news/feed/rss",
            # Additional reliable RSS feeds
            "foxnews": "https://moxie.foxnews.com/google-publisher/world.xml",
            "washingtonpost": "https://feeds.washingtonpost.com/rss/world",
            "usatoday": "https://rssfeeds.usatoday.com/UsatodaycomWorld-TopStories",
            "abcnews": "https://abcnews.go.com/abcnews/internationalheadlines",
            "yahoo": "https://www.yahoo.com/news/rss/world",
            "cbc": "https://rss.cbc.ca/lineup/world.xml",
            "skynews": "https://feeds.skynews.com/feeds/rss/world.xml",
            "cnbc": "https://www.cnbc.com/id/100727362/device/rss/rss.html",
            # Additional alternative sources
            "cnet": "https://www.cnet.com/rss/news/",
            "npr": "https://feeds.npr.org/1004/rss.xml",
            "aljazeera": "https://www.aljazeera.com/xml/rss/all.xml",
            "dw": "https://rss.dw.com/rdf/rss-en-all"
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # User agents for requests
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
        ]
    
    def get_news_from_rss(self, source="bbc", limit=10):
        """
        Get news from RSS feed
        
        Args:
            source (str): News source (key from rss_feeds dictionary)
            limit (int): Maximum number of news items to retrieve
            
        Returns:
            list: List of dictionaries with news items or empty list if error
        """
        try:
            if source not in self.rss_feeds:
                self.logger.warning(f"Source {source} not found in RSS feeds list")
                return []
            
            # Get and parse RSS feed
            feed_url = self.rss_feeds[source]
            
            # Use requests to get the RSS feed first to handle potential connection issues
            headers = {
                "User-Agent": self.user_agents[0],
                "Accept": "application/rss+xml, application/xml, text/xml; q=0.9, */*; q=0.8"
            }
            
            try:
                self.logger.info(f"Fetching RSS feed from {source}: {feed_url}")
                response = requests.get(feed_url, headers=headers, timeout=10)
                
                if response.status_code != 200:
                    self.logger.warning(f"Failed to get RSS feed {source} from {feed_url}, status: {response.status_code}")
                    # Try an alternative feed if available
                    if source == "ap":
                        feed_url = "https://storage.googleapis.com/afs-prod/feeds/world.rss.xml"
                        self.logger.info(f"Trying alternative feed for {source}: {feed_url}")
                        response = requests.get(feed_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    self.logger.info(f"Successfully fetched RSS feed from {source}")
                    feed = feedparser.parse(response.content)
                else:
                    self.logger.error(f"Error getting RSS feed {source}: status {response.status_code}")
                    return []
                    
            except requests.RequestException as e:
                self.logger.error(f"Request exception fetching RSS feed {source}: {str(e)}")
                # Try directly parsing the URL with feedparser as a fallback
                self.logger.info(f"Trying feedparser directly for {source}")
                feed = feedparser.parse(feed_url)
            
            # Check if there are items in the feed
            if not hasattr(feed, 'entries') or not feed.entries:
                self.logger.warning(f"No items in RSS feed {source}")
                return []
            
            # Create news list
            news_items = []
            
            # Limit number of news items
            entries = feed.entries[:min(limit, len(feed.entries))]
            self.logger.info(f"Processing {len(entries)} news entries from {source}")
            
            for entry in entries:
                # Basic data from RSS
                news_item = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", entry.get("pubDate", "")),
                    "description": entry.get("description", entry.get("summary", "")),
                    "full_text": ""
                }
                
                # Try to get full article text
                try:
                    full_text = self._extract_article_text(news_item["link"])
                    if full_text:
                        news_item["full_text"] = full_text
                except Exception as e:
                    self.logger.debug(f"Error getting full text for {news_item['link']}: {str(e)}")
                
                news_items.append(news_item)
            
            self.logger.info(f"Completed fetching {len(news_items)} news items from {source}")
            return news_items
            
        except Exception as e:
            self.logger.error(f"Error getting news from source {source}: {str(e)}")
            return []
    
    def _extract_article_text(self, url):
        """
        Extract article text from URL
        
        Args:
            url (str): Article URL
            
        Returns:
            str: Article text or empty string if error
        """
        try:
            import random
            
            # Send request with browser user agent
            headers = {
                "User-Agent": random.choice(self.user_agents),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none"
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                self.logger.debug(f"Failed to get page {url}, status: {response.status_code}")
                return ""
            
            # Parse page
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove scripts, styles and other unnecessary elements
            for element in soup(['script', 'style', 'header', 'footer', 'nav', 'aside', 'iframe', 'svg', 'form', 'button', 'noscript']):
                element.decompose()
            
            # Extract text from main content blocks
            # This is a simplified approach, each site may require its own logic
            text_blocks = []
            
            # Search for main content
            # Try various selectors commonly used for main content
            content_selectors = [
                "article", ".article", ".content", ".article-content", 
                ".article__text", ".story-body", ".story-content", 
                "#article-body", ".article-body", ".post-content",
                "main", ".main", "#main", "#content", ".post",
                ".news-article", ".story", ".entry-content", ".page-content",
                ".article__body", "[itemprop='articleBody']"
            ]
            
            # Try to find content by selectors
            for selector in content_selectors:
                content = soup.select(selector)
                if content:
                    for element in content:
                        # Add paragraph text
                        for p in element.find_all('p'):
                            if p.text.strip():
                                text_blocks.append(p.text.strip())
                    
                    # If content was found with one of the selectors, stop searching
                    if text_blocks:
                        break
            
            # If text couldn't be found by selectors, try to extract all paragraphs
            if not text_blocks:
                for p in soup.find_all('p'):
                    if p.text.strip() and len(p.text.strip()) > 50:  # Filter short paragraphs
                        text_blocks.append(p.text.strip())
            
            # Join paragraphs into single text
            result = "\n\n".join(text_blocks)
            
            # Limit result size to prevent overly large responses
            if len(result) > 50000:
                result = result[:50000] + "... [truncated]"
                
            return result
            
        except Exception as e:
            self.logger.debug(f"Error extracting text from {url}: {str(e)}")
            return ""

    def get_available_sources(self):
        """
        Returns list of available news sources
        """
        return list(self.rss_feeds.keys())

# Testing
if __name__ == "__main__":
    fetcher = NewsFetcher()
    print("Available sources:", fetcher.get_available_sources())
    news = fetcher.get_news_from_rss(source="bbc", limit=3)
    
    for item in news:
        print(f"Title: {item['title']}")
        print(f"Link: {item['link']}")
        print(f"Published: {item['published']}")
        print(f"Description: {item['description']}")
        print(f"Full text ({len(item['full_text'])} characters): {item['full_text'][:100]}...")
        print("-" * 80) 