"""
Unit tests for the Reddit API scraper module
"""

import unittest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.scraper import RedditScraper


class TestRedditAPIScraper(unittest.TestCase):
    """Test cases for Reddit API Scraper class"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_config = {
            'subreddits': ['test_subreddit'],
            'scraping': {
                'delay_min': 0.1,
                'delay_max': 0.2,
                'max_posts_per_subreddit': 5,
                'max_comments_per_post': 10
            },
            'reddit_api': {
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'user_agent': 'test_user_agent'
            },
            'database': {
                'type': 'sqlite',
                'sqlite': {'name': ':memory:'}
            },
            'processing': {'min_comment_length': 10}
        }

    @patch('src.scraper.RedditAPIScraper')
    @patch('src.scraper.load_config')
    def test_scraper_initialization(self, mock_load_config, mock_api_scraper):
        """Test scraper initialization"""
        mock_load_config.return_value = self.temp_config
        mock_api_instance = Mock()
        mock_api_scraper.return_value = mock_api_instance

        scraper = RedditScraper()

        self.assertEqual(scraper.config, self.temp_config)
        self.assertIsNotNone(scraper.api_scraper)
        mock_api_scraper.assert_called_once()

    @patch('src.scraper.RedditAPIScraper')
    @patch('src.scraper.load_config')
    def test_run_scraper(self, mock_load_config, mock_api_scraper):
        """Test running the scraper"""
        mock_load_config.return_value = self.temp_config
        mock_api_instance = Mock()
        mock_api_instance.run_api_scraper.return_value = {'test_subreddit': 5}
        mock_api_scraper.return_value = mock_api_instance

        scraper = RedditScraper()
        results = scraper.run_scraper()

        self.assertEqual(results, {'test_subreddit': 5})
        mock_api_instance.run_api_scraper.assert_called_once()

    @patch('src.scraper.RedditAPIScraper')
    @patch('src.scraper.load_config')
    def test_close_scraper(self, mock_load_config, mock_api_scraper):
        """Test closing the scraper"""
        mock_load_config.return_value = self.temp_config
        mock_api_instance = Mock()
        mock_api_scraper.return_value = mock_api_instance

        scraper = RedditScraper()
        scraper.close()

        mock_api_instance.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
