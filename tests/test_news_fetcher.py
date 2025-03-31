import pytest
from unittest.mock import patch, MagicMock
from news_fetcher import NewsFetcher

@pytest.fixture
def news_fetcher():
    """Create a NewsFetcher instance"""
    return NewsFetcher()

def test_get_available_sources(news_fetcher):
    """Test that available sources are returned as a list"""
    sources = news_fetcher.get_available_sources()
    assert isinstance(sources, list)
    assert len(sources) > 0
    assert "bbc" in sources

@patch('requests.get')
@patch('feedparser.parse')
def test_get_news_from_rss(mock_parse, mock_get, news_fetcher):
    """Test getting news from RSS feed"""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"RSS feed content"
    mock_get.return_value = mock_response
    
    mock_feed = MagicMock()
    mock_feed.entries = [
        {
            "title": "Test news title",
            "link": "https://example.com/news/1",
            "published": "Tue, 15 Mar 2023 12:00:00 GMT",
            "description": "Test news description"
        }
    ]
    mock_parse.return_value = mock_feed
    
    with patch.object(news_fetcher, '_extract_article_text', return_value="Full article text"):
        # Act
        news = news_fetcher.get_news_from_rss("bbc", 1)
        
        # Assert
        assert len(news) == 1
        assert news[0]["title"] == "Test news title"
        assert news[0]["link"] == "https://example.com/news/1"
        assert news[0]["published"] == "Tue, 15 Mar 2023 12:00:00 GMT"
        assert news[0]["description"] == "Test news description"
        assert news[0]["full_text"] == "Full article text"
        
        # Verify mocks were called correctly
        mock_get.assert_called_once()
        mock_parse.assert_called_once_with(mock_response.content)

@patch('requests.get')
def test_extract_article_text(mock_get, news_fetcher):
    """Test extracting text from an article"""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = """
    <html>
        <body>
            <article>
                <p>First paragraph of the article.</p>
                <p>Second paragraph with more <a href="#">details</a>.</p>
            </article>
        </body>
    </html>
    """
    mock_get.return_value = mock_response
    
    # Act
    text = news_fetcher._extract_article_text("https://example.com/news/1")
    
    # Assert
    assert "First paragraph of the article." in text
    assert "Second paragraph with more details." in text 