#!/usr/bin/env python3
"""
Debug script to analyze why posts are being removed during data processing
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.database_manager import create_database_manager
from src.utils import load_config, log_message


def analyze_posts():
    """Analyze posts in the database to understand why they're being removed"""
    print("🔍 ANALYZING POSTS IN DATABASE")
    print("=" * 50)
    
    try:
        config = load_config()
        db_manager = create_database_manager(config)
        db_manager.connect()
        
        # Get basic stats
        total_query = "SELECT COUNT(*) as count FROM posts"
        result = db_manager.execute_query(total_query)
        total_posts = result[0]['count'] if db_manager.db_type == 'mysql' else result[0][0]
        
        print(f"📊 Total posts in database: {total_posts}")
        
        if total_posts == 0:
            print("❌ No posts found in database!")
            print("   This suggests the posts were already deleted.")
            print("   You may need to re-run the scraper: python main.py --scrape")
            return
        
        # Check content lengths
        print("\n📏 CONTENT LENGTH ANALYSIS:")
        
        # Get sample posts with their content lengths
        sample_query = """
            SELECT id, question_title, 
                   LENGTH(answer_content_raw) as raw_length,
                   LENGTH(answer_content_cleaned) as cleaned_length,
                   answer_content_raw
            FROM posts 
            ORDER BY id 
            LIMIT 10
        """
        
        samples = db_manager.execute_query(sample_query)
        
        print("Sample posts:")
        for i, post in enumerate(samples, 1):
            if db_manager.db_type == 'mysql':
                post_id = post['id']
                title = post['question_title'][:50] if post['question_title'] else 'No title'
                raw_len = post['raw_length'] or 0
                cleaned_len = post['cleaned_length'] or 0
                raw_content = post['answer_content_raw'][:100] if post['answer_content_raw'] else 'No content'
            else:
                post_id = post[0]
                title = post[1][:50] if post[1] else 'No title'
                raw_len = post[2] or 0
                cleaned_len = post[3] or 0
                raw_content = post[4][:100] if post[4] else 'No content'
            
            print(f"  {i}. ID:{post_id} | Raw:{raw_len} | Cleaned:{cleaned_len}")
            print(f"     Title: {title}...")
            print(f"     Content: {raw_content}...")
            print()
        
        # Check processing configuration
        print("⚙️ PROCESSING CONFIGURATION:")
        min_length = config['processing']['min_comment_length']
        max_length = config['processing']['max_comment_length']
        print(f"  Min length: {min_length}")
        print(f"  Max length: {max_length}")
        
        # Count posts that would be removed by length filter
        length_filter_query = """
            SELECT COUNT(*) as count FROM posts 
            WHERE LENGTH(answer_content_cleaned) < %s 
            OR LENGTH(answer_content_cleaned) > %s
            OR answer_content_cleaned IS NULL
        """ if db_manager.db_type == 'mysql' else """
            SELECT COUNT(*) as count FROM posts 
            WHERE LENGTH(answer_content_cleaned) < ? 
            OR LENGTH(answer_content_cleaned) > ?
            OR answer_content_cleaned IS NULL
        """
        
        result = db_manager.execute_query(length_filter_query, (min_length, max_length))
        would_remove = result[0]['count'] if db_manager.db_type == 'mysql' else result[0][0]
        
        print(f"\n⚠️  Posts that would be removed by length filter: {would_remove}/{total_posts}")
        
        if would_remove == total_posts:
            print("❌ ALL POSTS WOULD BE REMOVED!")
            print("   This explains why all posts were deleted.")
            
            # Analyze why
            print("\n🔍 DETAILED ANALYSIS:")
            
            # Check for NULL cleaned content
            null_query = "SELECT COUNT(*) as count FROM posts WHERE answer_content_cleaned IS NULL"
            result = db_manager.execute_query(null_query)
            null_count = result[0]['count'] if db_manager.db_type == 'mysql' else result[0][0]
            print(f"  Posts with NULL cleaned content: {null_count}")
            
            # Check for too short content
            short_query = f"SELECT COUNT(*) as count FROM posts WHERE LENGTH(answer_content_cleaned) < {min_length}"
            result = db_manager.execute_query(short_query)
            short_count = result[0]['count'] if db_manager.db_type == 'mysql' else result[0][0]
            print(f"  Posts shorter than {min_length} chars: {short_count}")
            
            # Check for too long content
            long_query = f"SELECT COUNT(*) as count FROM posts WHERE LENGTH(answer_content_cleaned) > {max_length}"
            result = db_manager.execute_query(long_query)
            long_count = result[0]['count'] if db_manager.db_type == 'mysql' else result[0][0]
            print(f"  Posts longer than {max_length} chars: {long_count}")
            
            print("\n💡 SOLUTIONS:")
            if null_count > 0:
                print("  1. Run data processing first: python main.py --process")
                print("     (This will clean and populate answer_content_cleaned)")
            if short_count > 0:
                print(f"  2. Consider lowering min_comment_length from {min_length} to 10 or 5")
            if long_count > 0:
                print(f"  3. Consider raising max_comment_length from {max_length} to 10000")
        
        # Check processing status
        print(f"\n📝 PROCESSING STATUS:")
        processed_query = "SELECT COUNT(*) as count FROM posts WHERE processed_at IS NOT NULL"
        result = db_manager.execute_query(processed_query)
        processed_count = result[0]['count'] if db_manager.db_type == 'mysql' else result[0][0]
        print(f"  Processed posts: {processed_count}/{total_posts}")
        
        if processed_count == 0:
            print("⚠️  No posts have been processed yet!")
            print("   You should run processing BEFORE removing invalid data.")
            print("   Correct order:")
            print("   1. python main.py --scrape")
            print("   2. python main.py --process")
            print("   3. Then remove_invalid_data() will be called")
        
        db_manager.close()
        
    except Exception as e:
        print(f"❌ Error analyzing posts: {e}")
        import traceback
        traceback.print_exc()


def suggest_fixes():
    """Suggest fixes for the data processing issue"""
    print("\n🔧 SUGGESTED FIXES:")
    print("=" * 30)
    
    print("1. 📊 Check current data:")
    print("   python main.py --stats")
    
    print("\n2. 🔄 If posts were deleted, re-scrape:")
    print("   python main.py --scrape")
    
    print("\n3. ⚙️ Adjust processing parameters in config.yaml:")
    print("   processing:")
    print("     min_comment_length: 5    # Lower threshold")
    print("     max_comment_length: 10000  # Higher threshold")
    
    print("\n4. 📝 Run processing in correct order:")
    print("   python main.py --scrape   # Get data")
    print("   python main.py --process  # Clean data (without removing)")
    print("   # Then remove_invalid_data is called automatically")
    
    print("\n5. 🧪 Test with a small dataset first:")
    print("   # Modify config.yaml to scrape fewer posts")
    print("   scraping:")
    print("     max_posts_per_subreddit: 10")


def main():
    """Main debug function"""
    analyze_posts()
    suggest_fixes()


if __name__ == "__main__":
    main()
