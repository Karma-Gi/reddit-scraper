#!/usr/bin/env python3
"""
Quick test script for Reddit API functionality
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.reddit_api_scraper import RedditAPIScraper, test_reddit_api_connection
from src.utils import load_config, log_message


def test_api_basic():
    """Test basic API functionality"""
    print("🧪 TESTING REDDIT API BASIC FUNCTIONALITY")
    print("=" * 50)
    
    try:
        # Test connection
        print("1. Testing API connection...")
        if not test_reddit_api_connection():
            print("❌ API connection failed!")
            return False
        
        print("✅ API connection successful!")
        
        # Test scraper initialization
        print("\n2. Testing scraper initialization...")
        scraper = RedditAPIScraper()
        print("✅ Scraper initialized successfully!")
        
        # Test subreddit info
        print("\n3. Testing subreddit info retrieval...")
        info = scraper.get_subreddit_info("ApplyingToCollege")
        if info:
            print(f"✅ Subreddit info retrieved:")
            print(f"   Name: r/{info.get('name', 'N/A')}")
            print(f"   Title: {info.get('title', 'N/A')}")
            print(f"   Subscribers: {info.get('subscribers', 'N/A'):,}")
            print(f"   Created: {info.get('created', 'N/A')}")
        else:
            print("⚠️  Could not retrieve subreddit info")
        
        # Test search
        print("\n4. Testing search functionality...")
        search_results = scraper.search_posts("MIT", "ApplyingToCollege", limit=3)
        if search_results:
            print(f"✅ Found {len(search_results)} search results:")
            for i, result in enumerate(search_results, 1):
                print(f"   {i}. {result['title'][:50]}... (Score: {result['score']})")
        else:
            print("⚠️  No search results found")
        
        scraper.close()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_scraping():
    """Test actual scraping functionality"""
    print("\n🕷️ TESTING REDDIT API SCRAPING")
    print("=" * 40)
    
    try:
        config = load_config()
        
        # Temporarily modify config for testing
        original_subreddits = config['subreddits']
        original_max_posts = config['scraping']['max_posts_per_subreddit']
        
        config['subreddits'] = ['ApplyingToCollege']  # Test with one subreddit
        config['scraping']['max_posts_per_subreddit'] = 3  # Limit to 3 posts
        
        print(f"Testing with r/{config['subreddits'][0]}, max {config['scraping']['max_posts_per_subreddit']} posts")
        
        # Initialize scraper
        scraper = RedditAPIScraper()
        
        # Get initial database state
        initial_info = scraper.db_manager.get_table_info()
        initial_count = initial_info['total_posts']
        print(f"Initial posts in database: {initial_count}")
        
        # Run scraping
        print("\nStarting scraping test...")
        results = scraper.scrape_subreddit_api('ApplyingToCollege')
        
        # Check results
        print(f"\nScraping results: {results} posts")
        
        if results > 0:
            print("✅ Scraping successful!")
            
            # Check database
            final_info = scraper.db_manager.get_table_info()
            final_count = final_info['total_posts']
            new_posts = final_count - initial_count
            
            print(f"New posts added to database: {new_posts}")
            
            # Show sample data
            recent_posts = scraper.db_manager.execute_query("""
                SELECT question_title, LENGTH(answer_content_raw) as content_length
                FROM posts 
                ORDER BY created_at DESC 
                LIMIT 3
            """)
            
            print("\nSample scraped posts:")
            for i, post in enumerate(recent_posts, 1):
                if scraper.db_manager.db_type == 'mysql':
                    title = post['question_title'][:50] if post['question_title'] else 'No title'
                    length = post['content_length'] or 0
                else:
                    title = post[0][:50] if post[0] else 'No title'
                    length = post[1] or 0
                print(f"   {i}. {title}... ({length} chars)")
            
        else:
            print("⚠️  No posts scraped - this might be normal for testing")
        
        scraper.close()
        return True
        
    except Exception as e:
        print(f"❌ Scraping test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_api_status():
    """Show current API configuration status"""
    print("📋 REDDIT API STATUS")
    print("=" * 30)
    
    try:
        config = load_config()
        
        # Check scraping method
        method = config['scraping'].get('method', 'web')
        print(f"Scraping method: {method}")
        
        # Check API configuration
        api_config = config.get('reddit_api', {})
        client_id = api_config.get('client_id', 'NOT_SET')
        
        if client_id == 'YOUR_CLIENT_ID' or client_id == 'NOT_SET':
            print("❌ Reddit API not configured")
            print("   Run: python setup_reddit_api.py")
        else:
            print(f"✅ Reddit API configured")
            print(f"   Client ID: {client_id[:8]}...")
            print(f"   User Agent: {api_config.get('user_agent', 'NOT_SET')}")
            
            # Check if authenticated
            if api_config.get('username'):
                print(f"   Username: {api_config['username']}")
                print("   Mode: Authenticated")
            else:
                print("   Mode: Read-only")
        
        # Check database
        if method == 'api':
            from src.database_manager import create_database_manager
            db_manager = create_database_manager(config)
            db_manager.connect()
            info = db_manager.get_table_info()
            print(f"\nDatabase status:")
            print(f"   Type: {config['database']['type']}")
            print(f"   Total posts: {info['total_posts']}")
            db_manager.close()
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")


def main():
    """Main test function"""
    print("🧪 REDDIT API TEST SUITE")
    print("=" * 50)
    
    # Show current status
    show_api_status()
    
    # Check if API is configured
    try:
        config = load_config()
        api_config = config.get('reddit_api', {})
        client_id = api_config.get('client_id', 'NOT_SET')
        
        if client_id == 'YOUR_CLIENT_ID' or client_id == 'NOT_SET':
            print("\n❌ Reddit API not configured!")
            print("Please run: python setup_reddit_api.py")
            return
        
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    # Run tests
    print("\n" + "="*50)
    
    # Test 1: Basic functionality
    if not test_api_basic():
        print("\n❌ Basic tests failed!")
        return
    
    # Test 2: Scraping functionality
    response = input("\nRun scraping test? This will add data to your database (y/N): ").strip().lower()
    if response == 'y':
        if test_api_scraping():
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Scraping test failed!")
    else:
        print("\n⏭️  Skipped scraping test")
    
    print("\n" + "="*50)
    print("🎉 TEST COMPLETED!")
    print("\nNext steps:")
    print("• Run full scraper: python main.py --full")
    print("• View data: python main.py --view")
    print("• Check stats: python main.py --stats")


if __name__ == "__main__":
    main()
