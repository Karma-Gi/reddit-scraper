"""
Reddit API scraper for study abroad discussion data
Simplified version using only Reddit API
"""

from typing import Dict
from .reddit_api_scraper import RedditAPIScraper
from .utils import load_config, log_message


class RedditScraper:
    """Reddit API scraper for study abroad discussions"""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the Reddit API scraper"""
        self.config = load_config(config_path)
        self.api_scraper = RedditAPIScraper(config_path)
        self.db_manager = self.api_scraper.db_manager
        
    def run_scraper(self) -> Dict[str, int]:
        """Run the Reddit API scraping process"""
        log_message("Starting Reddit API scraper")
        return self.api_scraper.run_api_scraper()
    def close(self):
        """Close database connection and cleanup"""
        if hasattr(self, 'api_scraper'):
            self.api_scraper.close()
