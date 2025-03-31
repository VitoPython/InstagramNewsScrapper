import pytest
from unittest.mock import patch, MagicMock
from instagram_scraper import InstagramScraper
from datetime import datetime

@pytest.fixture
def mock_response():
    """Create a mock response object"""
    mock = MagicMock()
    mock.status_code = 200
    mock.text = """
    <html>
        <script type="text/javascript">window._sharedData = {
            "entry_data": {
                "ProfilePage": [{
                    "graphql": {
                        "user": {
                            "id": "12345",
                            "edge_owner_to_timeline_media": {
                                "edges": [
                                    {
                                        "node": {
                                            "shortcode": "ABC123",
                                            "edge_media_to_caption": {
                                                "edges": [
                                                    {
                                                        "node": {
                                                            "text": "Test post #test"
                                                        }
                                                    }
                                                ]
                                            },
                                            "edge_liked_by": {
                                                "count": 100
                                            },
                                            "edge_media_to_comment": {
                                                "count": 10
                                            },
                                            "taken_at_timestamp": 1623456789
                                        }
                                    }
                                ],
                                "page_info": {
                                    "has_next_page": false
                                }
                            }
                        }
                    }
                }]
            }
        };</script>
    </html>
    """
    return mock

@pytest.fixture
def scraper():
    """Create a scraper instance"""
    return InstagramScraper()

@patch('requests.get')
def test_scraper_extract_shared_data(mock_get, scraper, mock_response):
    """Test extracting shared data from HTML"""
    mock_get.return_value = mock_response
    
    shared_data = scraper._extract_shared_data(mock_response.text)
    
    assert shared_data is not None
    assert "entry_data" in shared_data
    assert "ProfilePage" in shared_data["entry_data"]

@patch('instagram_scraper.InstagramScraper._get_user_id')
@patch('instagram_scraper.InstagramScraper._get_posts_via_graphql')
def test_get_posts_success(mock_graphql, mock_user_id, scraper):
    """Test successful post retrieval"""
    # Arrange
    test_username = "testuser"
    mock_user_id.return_value = "12345"
    expected_posts = [
        {
            "url": "https://www.instagram.com/p/ABC123/",
            "text": "Test post #test",
            "title": "Test post",
            "likes": "100",
            "comments": "10",
            "hashtags": ["test"],
            "timestamp": datetime.fromtimestamp(1623456789).isoformat(),
            "username": test_username
        }
    ]
    mock_graphql.return_value = expected_posts
    
    # Act
    actual_posts = scraper.get_posts(test_username, 1)
    
    # Assert
    assert actual_posts == expected_posts
    mock_graphql.assert_called_once_with(test_username, 1) 