#!/usr/bin/env python3
"""
Usage examples for the Reddit Study Abroad Data Scraper
This file demonstrates how to use the different components of the system
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.scraper import RedditScraper
from src.data_processor import DataProcessor
from src.labeling_system import LabelingSystem
from src.utils import log_message
import sqlite3


def example_1_basic_scraping():
    """Example 1: Basic scraping workflow"""
    print("=" * 60)
    print("EXAMPLE 1: BASIC SCRAPING WORKFLOW")
    print("=" * 60)
    
    try:
        # Initialize scraper
        scraper = RedditScraper("config.yaml")
        
        # Run scraping for all configured subreddits
        results = scraper.run_scraper()
        
        # Display results
        print("\nScraping Results:")
        total_posts = 0
        for subreddit, count in results.items():
            print(f"  r/{subreddit}: {count} posts")
            total_posts += count
        
        print(f"\nTotal posts scraped: {total_posts}")
        
        # Clean up
        scraper.close()
        
    except Exception as e:
        print(f"Error in scraping example: {e}")


def example_2_data_processing():
    """Example 2: Data processing and cleaning"""
    print("=" * 60)
    print("EXAMPLE 2: DATA PROCESSING AND CLEANING")
    print("=" * 60)
    
    try:
        # Initialize processor
        processor = DataProcessor("config.yaml")
        
        # Process all posts
        print("Processing posts...")
        processed_count = processor.process_all_posts()
        print(f"Processed {processed_count} posts")
        
        # Remove invalid data
        print("\nRemoving invalid data...")
        removed_count = processor.remove_invalid_data()
        print(f"Removed {removed_count} invalid/duplicate posts")
        
        # Get processing statistics
        print("\nProcessing Statistics:")
        stats = processor.get_processing_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Example: Extract entities from a sample text
        sample_text = "I'm applying to MIT and Stanford for Computer Science PhD program"
        entities = processor.extract_entities(sample_text)
        print(f"\nEntity extraction example:")
        print(f"Text: {sample_text}")
        print(f"Universities: {entities['universities']}")
        print(f"Majors: {entities['majors']}")
        print(f"Programs: {entities['programs']}")
        
    except Exception as e:
        print(f"Error in processing example: {e}")


def example_3_labeling_system():
    """Example 3: Automatic labeling system"""
    print("=" * 60)
    print("EXAMPLE 3: AUTOMATIC LABELING SYSTEM")
    print("=" * 60)
    
    try:
        # Initialize labeling system
        labeler = LabelingSystem("config.yaml")
        
        # Example: Label individual texts
        test_texts = [
            "MIT is extremely difficult to get into. Very competitive program.",
            "This course was excellent! The professor was amazing and I learned so much.",
            "I absolutely love this university! Best decision ever!",
            "The program is okay, nothing special but not bad either."
        ]
        
        print("Individual text labeling examples:")
        for i, text in enumerate(test_texts, 1):
            print(f"\nExample {i}: {text}")
            results = labeler.label_post(i, text)
            
            print(f"  Difficulty: {results['difficulty_label']} (confidence: {results['difficulty_confidence']:.2f})")
            print(f"  Course Evaluation: {results['course_label']} (confidence: {results['course_confidence']:.2f})")
            print(f"  Sentiment: {results['sentiment_label']} (confidence: {results['sentiment_confidence']:.2f})")
            print(f"  Sentiment Score: {results['sentiment_score']:.1f}/10")
        
        # Label all posts in database
        print("\n" + "="*40)
        print("Labeling all posts in database...")
        labeled_count = labeler.label_all_posts()
        print(f"Labeled {labeled_count} posts")
        
        # Get labeling statistics
        print("\nLabeling Statistics:")
        stats = labeler.get_labeling_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"Error in labeling example: {e}")


def example_4_database_queries():
    """Example 4: Custom database queries and analysis"""
    print("=" * 60)
    print("EXAMPLE 4: DATABASE QUERIES AND ANALYSIS")
    print("=" * 60)
    
    try:
        # Connect to database
        conn = sqlite3.connect("reddit_study_abroad.db")
        cursor = conn.cursor()
        
        # Query 1: Top universities mentioned
        print("Top 10 universities mentioned:")
        cursor.execute("""
            SELECT university_name, COUNT(*) as mention_count
            FROM posts 
            WHERE university_name IS NOT NULL AND university_name != ''
            GROUP BY university_name 
            ORDER BY mention_count DESC 
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        for i, (university, count) in enumerate(results, 1):
            print(f"  {i}. {university}: {count} mentions")
        
        # Query 2: Sentiment distribution by subreddit
        print("\nSentiment distribution by subreddit:")
        cursor.execute("""
            SELECT subreddit, sentiment_label, COUNT(*) as count
            FROM posts 
            WHERE sentiment_label IS NOT NULL
            GROUP BY subreddit, sentiment_label
            ORDER BY subreddit, count DESC
        """)
        
        current_subreddit = None
        for subreddit, sentiment, count in cursor.fetchall():
            if subreddit != current_subreddit:
                print(f"\n  r/{subreddit}:")
                current_subreddit = subreddit
            print(f"    {sentiment}: {count} posts")
        
        # Query 3: Average sentiment score by university
        print("\nAverage sentiment score by university (top 5):")
        cursor.execute("""
            SELECT university_name, AVG(sentiment_score) as avg_sentiment, COUNT(*) as post_count
            FROM posts 
            WHERE university_name IS NOT NULL AND university_name != '' 
            AND sentiment_score IS NOT NULL
            GROUP BY university_name 
            HAVING post_count >= 3
            ORDER BY avg_sentiment DESC 
            LIMIT 5
        """)
        
        for university, avg_sentiment, post_count in cursor.fetchall():
            print(f"  {university}: {avg_sentiment:.1f}/10 ({post_count} posts)")
        
        # Query 4: Difficulty distribution
        print("\nApplication difficulty distribution:")
        cursor.execute("""
            SELECT difficulty_label, COUNT(*) as count
            FROM posts 
            WHERE difficulty_label IS NOT NULL
            GROUP BY difficulty_label
            ORDER BY 
                CASE difficulty_label 
                    WHEN '极难' THEN 1 
                    WHEN '难' THEN 2 
                    WHEN '中等' THEN 3 
                    WHEN '易' THEN 4 
                END
        """)
        
        for difficulty, count in cursor.fetchall():
            print(f"  {difficulty}: {count} posts")
        
        conn.close()
        
    except Exception as e:
        print(f"Error in database query example: {e}")


def example_5_full_pipeline():
    """Example 5: Complete pipeline execution"""
    print("=" * 60)
    print("EXAMPLE 5: COMPLETE PIPELINE EXECUTION")
    print("=" * 60)
    
    try:
        import time
        start_time = time.time()
        
        # Step 1: Scraping
        print("Step 1: Scraping data...")
        scraper = RedditScraper("config.yaml")
        scrape_results = scraper.run_scraper()
        scraper.close()
        
        total_scraped = sum(scrape_results.values())
        print(f"Scraped {total_scraped} posts")
        
        if total_scraped == 0:
            print("No data scraped. Skipping remaining steps.")
            return
        
        # Step 2: Processing
        print("\nStep 2: Processing data...")
        processor = DataProcessor("config.yaml")
        processed_count = processor.process_all_posts()
        removed_count = processor.remove_invalid_data()
        print(f"Processed {processed_count} posts, removed {removed_count} invalid posts")
        
        # Step 3: Labeling
        print("\nStep 3: Labeling data...")
        labeler = LabelingSystem("config.yaml")
        labeled_count = labeler.label_all_posts()
        print(f"Labeled {labeled_count} posts")
        
        # Final statistics
        print("\nFinal Statistics:")
        processing_stats = processor.get_processing_stats()
        labeling_stats = labeler.get_labeling_stats()
        
        print(f"  Total posts: {processing_stats['total_posts']}")
        print(f"  Processed posts: {processing_stats['processed_posts']}")
        print(f"  Labeled posts: {labeling_stats['total_labeled']}")
        print(f"  Posts with universities: {processing_stats['posts_with_universities']}")
        print(f"  Posts with majors: {processing_stats['posts_with_majors']}")
        print(f"  Average sentiment: {labeling_stats.get('average_sentiment_score', 'N/A')}")
        
        end_time = time.time()
        print(f"\nTotal execution time: {end_time - start_time:.2f} seconds")
        
    except Exception as e:
        print(f"Error in pipeline example: {e}")


def main():
    """Run all examples"""
    print("Reddit Study Abroad Data Scraper - Usage Examples")
    print("=" * 60)
    
    examples = [
        ("Basic Scraping", example_1_basic_scraping),
        ("Data Processing", example_2_data_processing),
        ("Labeling System", example_3_labeling_system),
        ("Database Queries", example_4_database_queries),
        ("Full Pipeline", example_5_full_pipeline)
    ]
    
    print("Available examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nChoose an example to run (1-5), or 'all' to run all examples:")
    choice = input("Enter your choice: ").strip().lower()
    
    if choice == 'all':
        for name, func in examples:
            print(f"\n{'='*80}")
            print(f"RUNNING: {name}")
            print(f"{'='*80}")
            func()
            print("\nPress Enter to continue to next example...")
            input()
    elif choice.isdigit() and 1 <= int(choice) <= len(examples):
        name, func = examples[int(choice) - 1]
        print(f"\nRunning: {name}")
        func()
    else:
        print("Invalid choice. Please run the script again.")


if __name__ == "__main__":
    main()
