"""
Reddit API scraper using PRAW (Python Reddit API Wrapper)
More reliable and efficient than web scraping
"""

import praw
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import re

from .database_manager import create_database_manager
from .utils import (
    load_config, clean_text, generate_content_hash, 
    is_valid_content, log_message, random_delay
)


class RedditAPIScraper:
    """Reddit scraper using official Reddit API"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize Reddit API scraper"""
        self.config = load_config(config_path)
        self.db_manager = create_database_manager(self.config)
        self.db_manager.connect()
        self.db_manager.setup_tables()
        
        # Initialize Reddit API client
        self.reddit = self._initialize_reddit_client()
        self.scraped_posts = set()
        
    def _initialize_reddit_client(self) -> praw.Reddit:
        """Initialize Reddit API client with configuration"""
        api_config = self.config['reddit_api']
        
        # Check if credentials are provided
        if api_config['client_id'] == "YOUR_CLIENT_ID":
            raise ValueError(
                "Reddit API credentials not configured. "
                "Please update config.yaml with your Reddit app credentials."
            )
        
        # Initialize PRAW client
        reddit_kwargs = {
            'client_id': api_config['client_id'],
            'client_secret': api_config['client_secret'],
            'user_agent': api_config['user_agent']
        }
        
        # Add username/password if provided (for authenticated access)
        if api_config.get('username') and api_config.get('password'):
            reddit_kwargs.update({
                'username': api_config['username'],
                'password': api_config['password']
            })
        
        reddit = praw.Reddit(**reddit_kwargs)
        
        # Test API connection
        try:
            # This will raise an exception if credentials are invalid
            reddit.user.me()
            log_message("✅ Reddit API authenticated successfully")
        except:
            log_message("✅ Reddit API connected (read-only mode)")
        
        return reddit
    
    def scrape_subreddit_api(self, subreddit_name: str) -> int:
        """Scrape a subreddit using Reddit API"""
        log_message(f"Starting to scrape r/{subreddit_name} using Reddit API")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts_scraped = 0
            max_posts = self.config['scraping']['max_posts_per_subreddit']
            
            # Get hot posts (you can also use .new(), .top(), etc.)
            for submission in subreddit.hot(limit=max_posts * 2):  # Get more to filter
                try:
                    # Skip stickied posts and announcements
                    if submission.stickied or submission.distinguished:
                        continue
                    
                    # Skip if already scraped
                    if submission.id in self.scraped_posts:
                        continue
                    
                    # Skip deleted or removed posts
                    if submission.selftext == '[deleted]' or submission.selftext == '[removed]':
                        continue
                    
                    # Get comments
                    comments = self._extract_comments_api(submission)
                    
                    # Only save posts with meaningful comments
                    if comments and len(comments) > 0:
                        self.save_api_post_data(
                            submission.id,
                            subreddit_name,
                            submission.title,
                            submission.selftext,  # Post content
                            comments,
                            f"https://reddit.com{submission.permalink}"
                        )
                        posts_scraped += 1
                        self.scraped_posts.add(submission.id)
                        
                        log_message(f"Saved post {submission.id}: {submission.title[:50]}...")
                    
                    # Stop if we've reached our target
                    if posts_scraped >= max_posts:
                        break
                    
                    # Rate limiting
                    random_delay(
                        self.config['scraping']['delay_min'],
                        self.config['scraping']['delay_max']
                    )
                    
                except Exception as e:
                    log_message(f"Error processing submission {submission.id}: {e}", "ERROR")
                    continue
            
            log_message(f"Completed scraping r/{subreddit_name}: {posts_scraped} posts")
            return posts_scraped
            
        except Exception as e:
            log_message(f"Error scraping r/{subreddit_name}: {e}", "ERROR")
            return 0
    
    def _extract_comments_api(self, submission) -> List[str]:
        """Extract comments from a Reddit submission"""
        comments = []
        max_comments = self.config['scraping']['max_comments_per_post']
        min_length = self.config['processing']['min_comment_length']
        
        try:
            # Expand comment tree (remove "more comments" objects)
            submission.comments.replace_more(limit=0)
            
            # Extract comments
            for comment in submission.comments.list()[:max_comments * 2]:  # Get more to filter
                if hasattr(comment, 'body') and comment.body:
                    # Skip deleted/removed comments
                    if comment.body in ['[deleted]', '[removed]']:
                        continue
                    
                    # Clean and validate comment
                    cleaned_comment = clean_text(comment.body)
                    if is_valid_content(cleaned_comment, min_length):
                        comments.append(cleaned_comment)
                        
                        # Stop if we have enough comments
                        if len(comments) >= max_comments:
                            break
            
        except Exception as e:
            log_message(f"Error extracting comments: {e}", "ERROR")
        
        return comments
    
    def save_api_post_data(self, post_id: str, subreddit: str, title: str, 
                          post_content: str, comments: List[str], post_url: str) -> None:
        """Save API scraped data to database"""
        # Combine post content and comments
        all_content = []
        if post_content and post_content.strip():
            all_content.append(post_content.strip())
        all_content.extend(comments)
        
        all_comments = "\n".join(all_content)
        content_hash = generate_content_hash(title + all_comments)
        
        # Check for duplicates
        check_query = "SELECT id FROM posts WHERE content_hash = %s" if self.db_manager.db_type == 'mysql' else "SELECT id FROM posts WHERE content_hash = ?"
        existing = self.db_manager.execute_query(check_query, (content_hash,))
        
        if existing:
            log_message(f"Duplicate content detected, skipping post {post_id}")
            return
        
        try:
            insert_query = """
                INSERT INTO posts (
                    post_id, subreddit, question_title, answer_content_raw, 
                    answer_content_cleaned, content_hash
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """ if self.db_manager.db_type == 'mysql' else """
                INSERT INTO posts (
                    post_id, subreddit, question_title, answer_content_raw, 
                    answer_content_cleaned, content_hash
                ) VALUES (?, ?, ?, ?, ?, ?)
            """
            
            self.db_manager.execute_update(insert_query, (
                post_id, subreddit, clean_text(title), all_comments, 
                clean_text(all_comments), content_hash
            ))
            
            log_message(f"Saved API post {post_id} with {len(comments)} comments")
            
        except Exception as e:
            log_message(f"Database error saving post {post_id}: {e}", "ERROR")
    
    def run_api_scraper(self) -> Dict[str, int]:
        """Run the complete API scraping process"""
        log_message("Starting Reddit API scraper")
        results = {}
        
        for subreddit in self.config['subreddits']:
            try:
                posts_count = self.scrape_subreddit_api(subreddit)
                results[subreddit] = posts_count
                
                # Create backup if configured
                if (self.config['database'].get('backup_enabled', False) and 
                    posts_count > 0):
                    from .utils import create_backup
                    if self.config['database']['type'] == 'sqlite':
                        backup_path = create_backup(self.config['database']['sqlite']['name'])
                        log_message(f"Created backup: {backup_path}")
                    
            except Exception as e:
                log_message(f"Error scraping r/{subreddit}: {e}", "ERROR")
                results[subreddit] = 0
        
        log_message(f"API scraping completed. Results: {results}")
        return results
    
    def get_subreddit_info(self, subreddit_name: str) -> Dict:
        """Get information about a subreddit"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            return {
                'name': subreddit.display_name,
                'title': subreddit.title,
                'description': subreddit.description[:200] + '...' if len(subreddit.description) > 200 else subreddit.description,
                'subscribers': subreddit.subscribers,
                'active_users': subreddit.active_user_count,
                'created': datetime.fromtimestamp(subreddit.created_utc).strftime('%Y-%m-%d'),
                'over18': subreddit.over18
            }
        except Exception as e:
            log_message(f"Error getting subreddit info for r/{subreddit_name}: {e}", "ERROR")
            return {}
    
    def search_posts(self, query: str, subreddit_name: str = None, limit: int = 10) -> List[Dict]:
        """Search for posts using Reddit API"""
        try:
            if subreddit_name:
                subreddit = self.reddit.subreddit(subreddit_name)
                search_results = subreddit.search(query, limit=limit, sort='relevance')
            else:
                search_results = self.reddit.subreddit('all').search(query, limit=limit, sort='relevance')
            
            results = []
            for submission in search_results:
                results.append({
                    'id': submission.id,
                    'title': submission.title,
                    'subreddit': submission.subreddit.display_name,
                    'score': submission.score,
                    'url': f"https://reddit.com{submission.permalink}",
                    'created': datetime.fromtimestamp(submission.created_utc).strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return results
            
        except Exception as e:
            log_message(f"Error searching posts: {e}", "ERROR")
            return []
    
    def close(self):
        """Close database connection"""
        if self.db_manager:
            self.db_manager.close()


def test_reddit_api_connection(config_path: str = "config.yaml") -> bool:
    """Test Reddit API connection"""
    try:
        config = load_config(config_path)
        api_config = config['reddit_api']
        
        if api_config['client_id'] == "YOUR_CLIENT_ID":
            log_message("❌ Reddit API credentials not configured", "ERROR")
            return False
        
        reddit = praw.Reddit(
            client_id=api_config['client_id'],
            client_secret=api_config['client_secret'],
            user_agent=api_config['user_agent']
        )
        
        # Test with a simple request
        test_subreddit = reddit.subreddit('test')
        test_post = next(test_subreddit.hot(limit=1))
        
        log_message("✅ Reddit API connection successful")
        return True
        
    except Exception as e:
        log_message(f"❌ Reddit API connection failed: {e}", "ERROR")
        return False
