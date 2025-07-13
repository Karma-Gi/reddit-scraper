#!/usr/bin/env python3
"""
Reddit Study Abroad Data Scraper - Main Application
Perfects.AI Data Science Internship Test Project

This is the main entry point for the Reddit scraper application.
It orchestrates the three main components:
1. Web scraping (Part 1)
2. Data processing (Part 2) 
3. Labeling system (Part 3)
"""

import argparse
import sys
import time
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.scraper import RedditScraper
from src.data_processor import DataProcessor
from src.labeling_system import LabelingSystem
from src.database_manager import create_database_manager
from src.data_viewer import DataViewer
from src.utils import log_message, load_config


def run_scraper(config_path: str = "config.yaml") -> bool:
    """Run the Reddit scraper (Part 1)"""
    log_message("=" * 50)
    log_message("PART 1: REDDIT SCRAPING")
    log_message("=" * 50)
    
    try:
        scraper = RedditScraper(config_path)
        results = scraper.run_scraper()
        scraper.close()
        
        total_posts = sum(results.values())
        log_message(f"Scraping completed successfully. Total posts: {total_posts}")
        
        if total_posts == 0:
            log_message("No posts were scraped. Please check your configuration and network connection.", "WARNING")
            return False
            
        return True
        
    except Exception as e:
        log_message(f"Error during scraping: {e}", "ERROR")
        return False


def run_data_processing(config_path: str = "config.yaml") -> bool:
    """Run data processing and cleaning (Part 2)"""
    log_message("=" * 50)
    log_message("PART 2: DATA PROCESSING")
    log_message("=" * 50)
    
    try:
        processor = DataProcessor(config_path)
        
        # Process all posts
        processed_count = processor.process_all_posts()
        log_message(f"Processed {processed_count} posts")
        
        # Remove invalid data
        removed_count = processor.remove_invalid_data()
        log_message(f"Removed {removed_count} invalid/duplicate posts")
        
        # Get processing statistics
        stats = processor.get_processing_stats()
        log_message("Processing Statistics:")
        for key, value in stats.items():
            log_message(f"  {key}: {value}")
        
        return processed_count > 0
        
    except Exception as e:
        log_message(f"Error during data processing: {e}", "ERROR")
        return False


def run_labeling(config_path: str = "config.yaml") -> bool:
    """Run the labeling system (Part 3)"""
    log_message("=" * 50)
    log_message("PART 3: LABELING SYSTEM")
    log_message("=" * 50)
    
    try:
        labeler = LabelingSystem(config_path)
        
        # Label all posts
        labeled_count = labeler.label_all_posts()
        log_message(f"Labeled {labeled_count} posts")
        
        # Get labeling statistics
        stats = labeler.get_labeling_stats()
        log_message("Labeling Statistics:")
        for key, value in stats.items():
            log_message(f"  {key}: {value}")
        
        return labeled_count > 0
        
    except Exception as e:
        log_message(f"Error during labeling: {e}", "ERROR")
        return False


def run_full_pipeline(config_path: str = "config.yaml") -> None:
    """Run the complete pipeline: scraping -> processing -> labeling"""
    start_time = time.time()
    
    log_message("Starting Reddit Study Abroad Data Scraper Pipeline")
    log_message(f"Configuration file: {config_path}")
    
    # Step 1: Scraping
    if not run_scraper(config_path):
        log_message("Pipeline failed at scraping stage", "ERROR")
        return
    
    # Step 2: Data Processing
    if not run_data_processing(config_path):
        log_message("Pipeline failed at data processing stage", "ERROR")
        return
    
    # Step 3: Labeling
    if not run_labeling(config_path):
        log_message("Pipeline failed at labeling stage", "ERROR")
        return
    
    # Pipeline completed successfully
    end_time = time.time()
    duration = end_time - start_time
    
    log_message("=" * 50)
    log_message("PIPELINE COMPLETED SUCCESSFULLY")
    log_message(f"Total execution time: {duration:.2f} seconds")
    log_message("=" * 50)


def show_stats(config_path: str = "config.yaml") -> None:
    """Show comprehensive statistics about the data"""
    try:
        config = load_config(config_path)
        db_manager = create_database_manager(config)
        db_manager.connect()

        viewer = DataViewer(db_manager)
        viewer.print_summary_report()

        db_manager.close()

    except Exception as e:
        log_message(f"Error showing statistics: {e}", "ERROR")


def interactive_data_viewer(config_path: str = "config.yaml") -> None:
    """Interactive data viewer for exploring scraped data"""
    try:
        config = load_config(config_path)
        db_manager = create_database_manager(config)
        db_manager.connect()
        viewer = DataViewer(db_manager)

        print("=" * 60)
        print("INTERACTIVE DATA VIEWER")
        print("=" * 60)

        while True:
            print("\nAvailable commands:")
            print("1. Show basic statistics")
            print("2. View recent posts")
            print("3. Search by university")
            print("4. Search by keyword")
            print("5. View sentiment analysis")
            print("6. View difficulty analysis")
            print("7. Export data to CSV")
            print("8. University rankings")
            print("9. Exit")

            choice = input("\nEnter your choice (1-9): ").strip()

            if choice == '1':
                viewer.print_summary_report()

            elif choice == '2':
                limit = input("Number of posts to show (default 10): ").strip()
                limit = int(limit) if limit.isdigit() else 10
                posts = viewer.get_recent_posts(limit)

                print(f"\n📝 RECENT {limit} POSTS:")
                for i, post in enumerate(posts, 1):
                    if db_manager.db_type == 'mysql':
                        print(f"{i}. [{post['subreddit']}] {post['question_title'][:80]}...")
                        print(f"   Sentiment: {post['sentiment_label']} ({post['sentiment_score']}/10)")
                    else:
                        print(f"{i}. [r/{post[1]}] {post[2][:80]}...")
                        print(f"   Sentiment: {post[4]} ({post[5]}/10)")

            elif choice == '3':
                university = input("Enter university name: ").strip()
                if university:
                    posts = viewer.get_posts_by_university(university)
                    print(f"\n🏫 POSTS ABOUT {university.upper()}:")
                    for i, post in enumerate(posts, 1):
                        if db_manager.db_type == 'mysql':
                            print(f"{i}. [{post['subreddit']}] {post['question_title'][:60]}...")
                            print(f"   Sentiment: {post['sentiment_score']}/10, Difficulty: {post['difficulty_label']}")
                        else:
                            print(f"{i}. [r/{post[1]}] {post[2][:60]}...")
                            print(f"   Sentiment: {post[8]}/10, Difficulty: {post[6]}")

            elif choice == '4':
                keyword = input("Enter search keyword: ").strip()
                if keyword:
                    posts = viewer.search_posts(keyword)
                    print(f"\n🔍 SEARCH RESULTS FOR '{keyword}':")
                    for i, post in enumerate(posts, 1):
                        if db_manager.db_type == 'mysql':
                            print(f"{i}. [{post['subreddit']}] {post['question_title'][:60]}...")
                            print(f"   University: {post['university_name']}, Sentiment: {post['sentiment_score']}/10")
                        else:
                            print(f"{i}. [r/{post[1]}] {post[2][:60]}...")
                            print(f"   University: {post[4]}, Sentiment: {post[7]}/10")

            elif choice == '5':
                sentiment_stats = viewer.get_sentiment_analysis()
                print("\n😊 SENTIMENT ANALYSIS:")

                print("\nOverall Distribution:")
                for item in sentiment_stats['sentiment_distribution']:
                    if db_manager.db_type == 'mysql':
                        print(f"  {item['sentiment_label']}: {item['count']} posts (avg: {item['avg_score']:.1f}/10)")
                    else:
                        print(f"  {item[0]}: {item[1]} posts (avg: {item[2]:.1f}/10)")

                print("\nMost Positive Posts:")
                for i, post in enumerate(sentiment_stats['most_positive'], 1):
                    if db_manager.db_type == 'mysql':
                        print(f"  {i}. {post['question_title'][:50]}... ({post['sentiment_score']}/10)")
                    else:
                        print(f"  {i}. {post[2][:50]}... ({post[3]}/10)")

            elif choice == '6':
                difficulty_stats = viewer.get_difficulty_analysis()
                print("\n📈 DIFFICULTY ANALYSIS:")

                print("\nOverall Distribution:")
                for item in difficulty_stats['difficulty_distribution']:
                    if db_manager.db_type == 'mysql':
                        print(f"  {item['difficulty_label']}: {item['count']} posts")
                    else:
                        print(f"  {item[0]}: {item[1]} posts")

            elif choice == '7':
                filename = input("Enter CSV filename (default: reddit_data.csv): ").strip()
                filename = filename if filename else "reddit_data.csv"
                viewer.export_to_csv(filename)
                print(f"✅ Data exported to {filename}")

            elif choice == '8':
                rankings = viewer.get_university_rankings()
                print("\n🏆 UNIVERSITY RANKINGS (by sentiment):")
                for i, uni in enumerate(rankings, 1):
                    if db_manager.db_type == 'mysql':
                        print(f"{i:2d}. {uni['university_name']:<20} | Sentiment: {uni['avg_sentiment']:4.1f}/10 | Mentions: {uni['mention_count']:3d}")
                    else:
                        print(f"{i:2d}. {uni[0]:<20} | Sentiment: {uni[2]:4.1f}/10 | Mentions: {uni[1]:3d}")

            elif choice == '9':
                break

            else:
                print("Invalid choice. Please try again.")

        db_manager.close()
        print("👋 Goodbye!")

    except Exception as e:
        log_message(f"Error in data viewer: {e}", "ERROR")


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Reddit Study Abroad Data Scraper - Perfects.AI Internship Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --full                    # Run complete pipeline (API scraping)
  python main.py --scrape                  # Run only Reddit API scraping
  python main.py --process                 # Run only data processing
  python main.py --label                   # Run only labeling
  python main.py --stats                   # Show database statistics
  python main.py --view                    # Interactive data viewer
  python main.py --test-api                # Test Reddit API connection
  python main.py --config custom.yaml     # Use custom configuration
        """
    )
    
    parser.add_argument("--config", "-c", default="config.yaml",
                       help="Configuration file path (default: config.yaml)")
    parser.add_argument("--full", action="store_true",
                       help="Run complete pipeline (scrape -> process -> label)")
    parser.add_argument("--scrape", action="store_true",
                       help="Run only the scraping component")
    parser.add_argument("--process", action="store_true",
                       help="Run only the data processing component")
    parser.add_argument("--label", action="store_true",
                       help="Run only the labeling component")
    parser.add_argument("--stats", action="store_true",
                       help="Show database statistics")
    parser.add_argument("--view", action="store_true",
                       help="Launch interactive data viewer")
    parser.add_argument("--export", type=str, metavar="FILENAME",
                       help="Export data to CSV file")
    parser.add_argument("--test-api", action="store_true",
                       help="Test Reddit API connection")
    parser.add_argument("--setup-api", action="store_true",
                       help="Setup Reddit API credentials")
    
    args = parser.parse_args()
    
    # Check if config file exists
    if not Path(args.config).exists():
        log_message(f"Configuration file {args.config} not found", "ERROR")
        sys.exit(1)
    
    # Execute based on arguments
    if args.full:
        run_full_pipeline(args.config)
    elif args.scrape:
        run_scraper(args.config)
    elif args.process:
        run_data_processing(args.config)
    elif args.label:
        run_labeling(args.config)
    elif args.stats:
        show_stats(args.config)
    elif args.view:
        interactive_data_viewer(args.config)
    elif args.export:
        try:
            config = load_config(args.config)
            db_manager = create_database_manager(config)
            db_manager.connect()
            viewer = DataViewer(db_manager)
            viewer.export_to_csv(args.export)
            db_manager.close()
        except Exception as e:
            log_message(f"Export failed: {e}", "ERROR")
    elif args.test_api:
        try:
            from src.reddit_api_scraper import test_reddit_api_connection
            if test_reddit_api_connection(args.config):
                print("✅ Reddit API connection successful!")
            else:
                print("❌ Reddit API connection failed!")
        except ImportError:
            print("❌ PRAW not installed. Run: pip install praw")
        except Exception as e:
            log_message(f"API test failed: {e}", "ERROR")
    elif args.setup_api:
        try:
            import subprocess
            subprocess.run([sys.executable, "setup_reddit_api.py"])
        except Exception as e:
            log_message(f"Setup failed: {e}", "ERROR")
    else:
        # Default: show help and run full pipeline
        parser.print_help()
        print("\nNo specific action specified. Running full pipeline...\n")
        run_full_pipeline(args.config)


if __name__ == "__main__":
    main()
