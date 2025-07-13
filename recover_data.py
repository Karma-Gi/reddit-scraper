#!/usr/bin/env python3
"""
Data recovery and safe processing script
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.database_manager import create_database_manager
from src.scraper import RedditScraper
from src.data_processor import DataProcessor
from src.utils import load_config, log_message


def check_data_status():
    """Check current data status"""
    print("📊 CHECKING DATA STATUS")
    print("=" * 30)
    
    try:
        config = load_config()
        db_manager = create_database_manager(config)
        db_manager.connect()
        
        # Get basic stats
        total_query = "SELECT COUNT(*) as count FROM posts"
        result = db_manager.execute_query(total_query)
        total_posts = result[0]['count'] if db_manager.db_type == 'mysql' else result[0][0]
        
        print(f"Total posts in database: {total_posts}")
        
        if total_posts == 0:
            print("❌ No posts found! Data needs to be re-scraped.")
            return False
        
        # Check processing status
        processed_query = "SELECT COUNT(*) as count FROM posts WHERE processed_at IS NOT NULL"
        result = db_manager.execute_query(processed_query)
        processed_count = result[0]['count'] if db_manager.db_type == 'mysql' else result[0][0]
        
        print(f"Processed posts: {processed_count}/{total_posts}")
        
        # Check content lengths
        if processed_count > 0:
            length_query = """
                SELECT 
                    MIN(LENGTH(answer_content_cleaned)) as min_len,
                    MAX(LENGTH(answer_content_cleaned)) as max_len,
                    AVG(LENGTH(answer_content_cleaned)) as avg_len
                FROM posts 
                WHERE answer_content_cleaned IS NOT NULL
            """
            result = db_manager.execute_query(length_query)
            if result:
                if db_manager.db_type == 'mysql':
                    min_len, max_len, avg_len = result[0]['min_len'], result[0]['max_len'], result[0]['avg_len']
                else:
                    min_len, max_len, avg_len = result[0][0], result[0][1], result[0][2]
                
                print(f"Content lengths - Min: {min_len}, Max: {max_len}, Avg: {avg_len:.1f}")
        
        # Show sample posts
        sample_query = """
            SELECT question_title, LENGTH(answer_content_raw) as raw_len
            FROM posts 
            ORDER BY id 
            LIMIT 5
        """
        samples = db_manager.execute_query(sample_query)
        
        print("\nSample posts:")
        for i, post in enumerate(samples, 1):
            if db_manager.db_type == 'mysql':
                title = post['question_title'][:50] if post['question_title'] else 'No title'
                raw_len = post['raw_len'] or 0
            else:
                title = post[0][:50] if post[0] else 'No title'
                raw_len = post[1] or 0
            print(f"  {i}. {title}... ({raw_len} chars)")
        
        db_manager.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking data status: {e}")
        return False


def safe_data_processing():
    """Safely process data with preview"""
    print("\n🔧 SAFE DATA PROCESSING")
    print("=" * 30)
    
    try:
        processor = DataProcessor()
        
        # First, process posts (clean and extract entities)
        print("📝 Step 1: Processing posts...")
        processed_count = processor.process_all_posts()
        print(f"✅ Processed {processed_count} posts")
        
        if processed_count == 0:
            print("⚠️  No posts were processed. They may already be processed.")
        
        # Preview what would be removed
        print("\n🔍 Step 2: Previewing data removal...")
        processor._log_removal_preview()
        
        # Ask user for confirmation
        response = input("\nDo you want to proceed with removing invalid data? (y/N): ").strip().lower()
        
        if response == 'y':
            print("🗑️ Step 3: Removing invalid data...")
            removed_count = processor.remove_invalid_data()
            print(f"✅ Removed {removed_count} invalid posts")
        else:
            print("⏭️  Skipped data removal")
        
        # Show final stats
        stats = processor.get_processing_stats()
        print(f"\n📊 Final stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in safe processing: {e}")
        import traceback
        traceback.print_exc()
        return False


def recover_data():
    """Re-scrape data if needed"""
    print("\n🔄 DATA RECOVERY")
    print("=" * 20)
    
    response = input("Do you want to re-scrape data from Reddit? (y/N): ").strip().lower()
    
    if response == 'y':
        try:
            print("🕷️ Starting Reddit API scraper...")
            scraper = RedditScraper()
            results = scraper.run_scraper()
            scraper.close()
            
            total_scraped = sum(results.values())
            print(f"✅ Scraped {total_scraped} new posts")
            
            if total_scraped > 0:
                print("📊 Results by subreddit:")
                for subreddit, count in results.items():
                    print(f"  r/{subreddit}: {count} posts")
            
            return total_scraped > 0
            
        except Exception as e:
            print(f"❌ Error during re-scraping: {e}")
            return False
    else:
        print("⏭️  Skipped data recovery")
        return False


def main():
    """Main recovery function"""
    print("🚑 DATA RECOVERY AND SAFE PROCESSING TOOL")
    print("=" * 50)
    
    # Step 1: Check current status
    has_data = check_data_status()
    
    # Step 2: Recover data if needed
    if not has_data:
        print("\n💡 Data recovery needed!")
        recovered = recover_data()
        if not recovered:
            print("❌ Cannot proceed without data")
            return
    
    # Step 3: Safe processing
    print("\n" + "="*50)
    safe_data_processing()
    
    print("\n" + "="*50)
    print("🎉 RECOVERY COMPLETED!")
    print("\nNext steps:")
    print("  • Check data: python main.py --stats")
    print("  • View data: python main.py --view")
    print("  • Run labeling: python main.py --label")


if __name__ == "__main__":
    main()
