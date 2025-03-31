import requests
import json
import re
import random
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import time
from typing import List, Dict, Any

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Disable unnecessary logs from libraries
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

class InstagramScraper:
    """Class for scraping data from public Instagram accounts"""
    
    def __init__(self):
        """Initialize scraper with settings for HTTP requests"""
        # List of User-Agent strings to simulate different browsers
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        ]
        
        # Basic headers for requests
        self.headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.instagram.com/',
            'sec-ch-ua': '"Chromium";v="122", "Google Chrome";v="122", "Not:A-Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # Add cookies and token for authentication - important for real scraping
        self.cookies = {
            'ig_did': f'{self._generate_ig_did()}',
            'mid': f'{self._generate_mid()}',
            'csrftoken': f'{self._generate_csrftoken()}',
            'ds_user_id': '',
            'sessionid': '',
            'rur': '"RVA,{}"'.format(''.join(random.choice("0123456789") for _ in range(10)))
        }
    
    def get_posts(self, username, num_posts=10):
        """
        Get recent posts from Instagram account
        
        Args:
            username (str): Instagram username (without @)
            num_posts (int): Number of posts to retrieve
            
        Returns:
            list: List of posts with metadata
        """
        all_posts = []
        
        try:
            logger.info(f"Scraping data for @{username}")
            
            # Try all methods silently
            all_posts = self._get_posts_via_graphql(username, num_posts)
            
            if not all_posts:
                all_posts = self._get_posts_via_html(username, num_posts)
                
            if not all_posts:
                all_posts = self._get_posts_via_alternative_api(username, num_posts)
                
            # If all methods failed, raise exception
            if not all_posts:
                raise Exception("Failed to get data")
                
            logger.info(f"Retrieved {len(all_posts)} posts")
            return all_posts[:num_posts]
            
        except Exception as e:
            # Only log the exception without details
            logger.error(f"Scraping failed for @{username}")
            raise Exception(f"Scraping failed")
    
    def _get_posts_via_graphql(self, username, num_posts):
        """Get posts via GraphQL API"""
        posts = []
        
        try:
            # Request to Instagram to get user ID
            user_id = self._get_user_id(username)
            
            if not user_id:
                return []
                
            # Query GraphQL API for posts
            query_hash = "472f257a40c653c64c666ce877d59d2b"  # Current hash for media query (updated periodically)
            
            variables = {
                "id": user_id,
                "first": min(num_posts, 50),  # Maximum 50 posts per request
                "after": None
            }
            
            url = f"https://www.instagram.com/graphql/query/?query_hash={query_hash}&variables={json.dumps(variables)}"
            
            # Simulate delay like a normal user
            time.sleep(random.uniform(2, 4))
            
            # Update User-Agent for each request
            self.headers['User-Agent'] = random.choice(self.user_agents)
            
            # Make request
            response = requests.get(
                url, 
                headers=self.headers, 
                cookies=self.cookies,
                timeout=10
            )
            
            if response.status_code != 200:
                return []
                
            data = response.json()
            
            # Extract post data
            user_data = data.get('data', {}).get('user', {})
            if not user_data:
                return []
                
            edge_owner_to_timeline_media = user_data.get('edge_owner_to_timeline_media', {})
            edges = edge_owner_to_timeline_media.get('edges', [])
            
            # Process each post
            for edge in edges:
                node = edge.get('node', {})
                
                if not node:
                    continue
                
                post = self._extract_post_from_node(node, username)
                posts.append(post)
            
            # Check if we need to request additional posts with pagination
            page_info = edge_owner_to_timeline_media.get('page_info', {})
            has_next_page = page_info.get('has_next_page', False)
            end_cursor = page_info.get('end_cursor')
            
            # Request additional pages if not enough posts
            while has_next_page and len(posts) < num_posts:
                # Update variables for next request
                variables["after"] = end_cursor
                
                # Update URL
                url = f"https://www.instagram.com/graphql/query/?query_hash={query_hash}&variables={json.dumps(variables)}"
                
                # Simulate delay
                time.sleep(random.uniform(3, 6))
                
                # Update User-Agent
                self.headers['User-Agent'] = random.choice(self.user_agents)
                
                # Make request
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    cookies=self.cookies,
                    timeout=15
                )
                
                if response.status_code != 200:
                    break
                    
                data = response.json()
                
                # Extract post data
                user_data = data.get('data', {}).get('user', {})
                edge_owner_to_timeline_media = user_data.get('edge_owner_to_timeline_media', {})
                edges = edge_owner_to_timeline_media.get('edges', [])
                
                # Process each post
                for edge in edges:
                    if len(posts) >= num_posts:
                        break
                        
                    node = edge.get('node', {})
                    
                    if not node:
                        continue
                    
                    post = self._extract_post_from_node(node, username)
                    posts.append(post)
                
                # Check if there are more pages
                page_info = edge_owner_to_timeline_media.get('page_info', {})
                has_next_page = page_info.get('has_next_page', False) and len(posts) < num_posts
                end_cursor = page_info.get('end_cursor')
            
        except Exception:
            # Silently fail and return empty list
            return []
        
        return posts
    
    def _get_posts_via_html(self, username, num_posts):
        """Get posts by parsing profile HTML page"""
        posts = []
        
        try:
            # Get profile page
            url = f"https://www.instagram.com/{username}/"
            
            # Simulate delay
            time.sleep(random.uniform(1, 3))
            
            # Update User-Agent
            self.headers['User-Agent'] = random.choice(self.user_agents)
            
            # Make request
            response = requests.get(
                url, 
                headers=self.headers, 
                cookies=self.cookies,
                timeout=10
            )
            
            if response.status_code != 200:
                return []
            
            # Get shared_data from HTML
            shared_data = self._extract_shared_data(response.text)
            
            if not shared_data:
                return []
            
            # Extract profile and post data
            user_data = None
            
            # Search in main format
            if 'entry_data' in shared_data and 'ProfilePage' in shared_data['entry_data']:
                if len(shared_data['entry_data']['ProfilePage']) > 0:
                    if 'graphql' in shared_data['entry_data']['ProfilePage'][0]:
                        if 'user' in shared_data['entry_data']['ProfilePage'][0]['graphql']:
                            user_data = shared_data['entry_data']['ProfilePage'][0]['graphql']['user']
            
            # Search in alternative format
            if not user_data and 'user' in shared_data:
                user_data = shared_data['user']
            
            if not user_data:
                return []
            
            # Extract node with posts
            edge_owner_to_timeline_media = user_data.get('edge_owner_to_timeline_media')
            
            if not edge_owner_to_timeline_media:
                return []
            
            # Iterate through posts
            for edge in edge_owner_to_timeline_media.get('edges', []):
                node = edge.get('node', {})
                
                if not node:
                    continue
                
                post = self._extract_post_from_node(node, username)
                posts.append(post)
            
        except Exception:
            # Silently fail and return empty list
            return []
        
        return posts
    
    def _get_posts_via_alternative_api(self, username, num_posts):
        """Get posts via alternative API"""
        posts = []
        
        try:
            # Use Instagram's public API to get first 12 posts
            url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
            
            # Simulate delay
            time.sleep(random.uniform(2, 4))
            
            # Add special headers for this API
            headers = self.headers.copy()
            headers['X-IG-App-ID'] = '936619743392459'  # Important header for this API
            headers['X-Requested-With'] = 'XMLHttpRequest'
            
            # Make request
            response = requests.get(
                url, 
                headers=headers, 
                cookies=self.cookies,
                timeout=10
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            
            # Extract user and post information
            user_data = data.get('data', {}).get('user', {})
            if not user_data:
                return []
            
            edge_owner_to_timeline_media = user_data.get('edge_owner_to_timeline_media', {})
            edges = edge_owner_to_timeline_media.get('edges', [])
            
            # Process each post
            for edge in edges:
                node = edge.get('node', {})
                
                if not node:
                    continue
                
                post = self._extract_post_from_node(node, username)
                posts.append(post)
            
            # If we need more posts, use pagination
            if len(posts) < num_posts:
                # Get pagination information
                page_info = edge_owner_to_timeline_media.get('page_info', {})
                has_next_page = page_info.get('has_next_page', False)
                end_cursor = page_info.get('end_cursor')
                
                if has_next_page and end_cursor:
                    user_id = user_data.get('id')
                    additional_posts = self._get_more_posts_via_api(user_id, end_cursor, num_posts - len(posts))
                    posts.extend(additional_posts)
            
        except Exception:
            # Silently fail and return empty list
            return []
        
        return posts
    
    def _get_more_posts_via_api(self, user_id, end_cursor, num_posts):
        """Get additional posts via API with pagination"""
        additional_posts = []
        
        try:
            # Form URL for requesting additional posts
            variables = {
                "id": user_id,
                "first": min(num_posts, 50),
                "after": end_cursor
            }
            
            url = f"https://www.instagram.com/graphql/query/?query_hash=e769aa130647d2354c40ea6a439bfc08&variables={json.dumps(variables)}"
            
            # Simulate delay
            time.sleep(random.uniform(3, 5))
            
            # Update User-Agent
            self.headers['User-Agent'] = random.choice(self.user_agents)
            
            # Make request
            response = requests.get(
                url, 
                headers=self.headers, 
                cookies=self.cookies,
                timeout=15
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            
            # Extract post data
            user_data = data.get('data', {}).get('user', {})
            edge_owner_to_timeline_media = user_data.get('edge_owner_to_timeline_media', {})
            edges = edge_owner_to_timeline_media.get('edges', [])
            
            # Process each post
            for edge in edges:
                node = edge.get('node', {})
                
                if not node:
                    continue
                
                # Extract post information
                post = self._extract_post_from_node(node, "")  # Username will be filled later
                additional_posts.append(post)
            
        except Exception:
            # Silently fail
            pass
        
        return additional_posts
    
    def _extract_post_from_node(self, node, username):
        """Extract post information from GraphQL node"""
        try:
            # Basic post information
            post_url = f"https://www.instagram.com/p/{node.get('shortcode', '')}/"
            
            # Extract caption
            caption_node = node.get('edge_media_to_caption', {}).get('edges', [])
            caption = caption_node[0]['node']['text'] if caption_node else ""
            
            # Extract hashtags
            hashtags = []
            for tag in re.findall(r'#(\w+)', caption):
                hashtags.append(tag.lower())
            
            # Form title from first 30 characters of text
            title = caption[:30] + ("..." if len(caption) > 30 else "")
            
            # Gather information about likes and comments
            likes = str(node.get('edge_liked_by', {}).get('count', 0) or node.get('edge_media_preview_like', {}).get('count', 0))
            comments = str(node.get('edge_media_to_comment', {}).get('count', 0))
            
            # Create publication date
            timestamp = datetime.fromtimestamp(node.get('taken_at_timestamp', 0))
            
            # If username is not specified, try to extract it from node
            if not username:
                owner = node.get('owner', {})
                username = owner.get('username', "")
            
            # Create post object
            post = {
                "url": post_url,
                "text": caption,
                "title": title,
                "likes": likes,
                "comments": comments,
                "hashtags": hashtags,
                "timestamp": timestamp.isoformat(),
                "username": username
            }
            
            return post
            
        except Exception:
            # Return empty post in case of error
            return {
                "url": "",
                "text": "",
                "title": "",
                "likes": "0",
                "comments": "0",
                "hashtags": [],
                "timestamp": datetime.now().isoformat(),
                "username": username
            }
    
    def _extract_shared_data(self, html):
        """Extract shared_data from Instagram HTML page"""
        try:
            # Look for shared_data block
            match = re.search(r'window\._sharedData\s*=\s*(.+?);</script>', html)
            
            if match:
                json_str = match.group(1)
                return json.loads(json_str)
            
            # Alternative search in different format
            match = re.search(r'window\.__additionalDataLoaded\s*\(\s*[\'"]profile[\'"],\s*(.+?)\s*\);</script>', html)
            
            if match:
                json_str = match.group(1)
                return json.loads(json_str)
                
            # Another format (new Instagram)
            match = re.search(r'<script type="application/json" data-sjs>(.+?)</script>', html)
            
            if match:
                json_str = match.group(1)
                data = json.loads(json_str)
                
                # Now need to find user data in this structure
                if 'require' in data:
                    for item in data['require']:
                        if isinstance(item, list) and len(item) > 2 and isinstance(item[2], dict):
                            if 'user' in item[2]:
                                return item[2]
            
            return None
            
        except Exception:
            return None
    
    def _get_user_id(self, username):
        """Get Instagram user ID"""
        try:
            # Request user information
            url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
            
            # Simulate delay
            time.sleep(random.uniform(1, 2))
            
            # Update User-Agent
            self.headers['User-Agent'] = random.choice(self.user_agents)
            
            # Make request
            response = requests.get(
                url, 
                headers=self.headers, 
                cookies=self.cookies,
                timeout=10
            )
            
            if response.status_code != 200:
                # Try alternative method - via HTML page
                return self._get_user_id_from_html(username)
            
            # Parse JSON response
            data = response.json()
            
            # Response structure may vary
            if 'graphql' in data and 'user' in data['graphql']:
                return data['graphql']['user']['id']
            elif 'user' in data:
                return data['user']['id']
            else:
                # Try alternative method - via HTML page
                return self._get_user_id_from_html(username)
            
        except Exception:
            # Try alternative method - via HTML page
            return self._get_user_id_from_html(username)
    
    def _get_user_id_from_html(self, username):
        """Get user ID from HTML page"""
        try:
            # Request user page
            url = f"https://www.instagram.com/{username}/"
            
            # Simulate delay
            time.sleep(random.uniform(2, 3))
            
            # Update User-Agent
            self.headers['User-Agent'] = random.choice(self.user_agents)
            
            # Make request
            response = requests.get(
                url, 
                headers=self.headers, 
                cookies=self.cookies,
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            # Look for user ID in HTML
            # Option 1: look in shared_data
            shared_data = self._extract_shared_data(response.text)
            
            if shared_data:
                # Search in main format
                if 'entry_data' in shared_data and 'ProfilePage' in shared_data['entry_data']:
                    if len(shared_data['entry_data']['ProfilePage']) > 0:
                        if 'graphql' in shared_data['entry_data']['ProfilePage'][0]:
                            if 'user' in shared_data['entry_data']['ProfilePage'][0]['graphql']:
                                return shared_data['entry_data']['ProfilePage'][0]['graphql']['user'].get('id')
                
                # Search in alternative format
                if 'user' in shared_data:
                    return shared_data['user'].get('id')
            
            # Option 2: regular expressions
            match = re.search(r'"user_id":"(\d+)"', response.text)
            if match:
                return match.group(1)
                
            match = re.search(r'"profilePage_(\d+)"', response.text)
            if match:
                return match.group(1)
                
            # Option 3: reading meta data
            soup = BeautifulSoup(response.text, 'html.parser')
            for meta in soup.find_all('meta'):
                if 'property' in meta.attrs and meta.attrs['property'] == 'al:ios:url':
                    content = meta.attrs.get('content', '')
                    match = re.search(r'user\?id=(\d+)', content)
                    if match:
                        return match.group(1)
            
            return None
            
        except Exception:
            return None
    
    def _generate_ig_did(self):
        """Generate random ig_did for headers"""
        return ''.join(random.choice("0123456789abcdef") for _ in range(32))
    
    def _generate_mid(self):
        """Generate random mid for headers"""
        return ''.join(random.choice("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(26))
    
    def _generate_csrftoken(self):
        """Generate random csrftoken for headers"""
        return ''.join(random.choice("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(32))
    
    def _generate_random_id(self, length=11):
        """Generate random Instagram-style post ID"""
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
        return ''.join(random.choice(chars) for _ in range(length))

if __name__ == "__main__":
    scraper = InstagramScraper()
    try:
        posts = scraper.get_posts("nasa", 5)
        print(json.dumps(posts, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Scraping failed")
        print("Instagram may have blocked requests or API changed")
        print("Please check your connection or try again later.") 