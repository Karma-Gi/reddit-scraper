"""
Data viewer for Reddit scraper database
Provides various ways to query and display scraped data
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from .database_manager import DatabaseManager
from .utils import log_message


class DataViewer:
    """Data viewer for analyzing scraped Reddit data"""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize data viewer with database manager"""
        self.db_manager = db_manager
    
    def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the data"""
        return self.db_manager.get_table_info()
    
    def get_recent_posts(self, limit: int = 10) -> List[Dict]:
        """Get most recent posts"""
        query = """
            SELECT post_id, subreddit, question_title, 
                   difficulty_label, sentiment_label, sentiment_score,
                   created_at
            FROM posts 
            ORDER BY created_at DESC 
            LIMIT %s
        """ if self.db_manager.db_type == 'mysql' else """
            SELECT post_id, subreddit, question_title, 
                   difficulty_label, sentiment_label, sentiment_score,
                   created_at
            FROM posts 
            ORDER BY created_at DESC 
            LIMIT ?
        """
        
        return self.db_manager.execute_query(query, (limit,))
    
    def get_posts_by_subreddit(self, subreddit: str, limit: int = 20) -> List[Dict]:
        """Get posts from specific subreddit"""
        query = """
            SELECT post_id, question_title, answer_content_cleaned,
                   university_name, major_name, program_name,
                   difficulty_label, course_evaluation_label, sentiment_label,
                   sentiment_score, created_at
            FROM posts 
            WHERE subreddit = %s
            ORDER BY created_at DESC
            LIMIT %s
        """ if self.db_manager.db_type == 'mysql' else """
            SELECT post_id, question_title, answer_content_cleaned,
                   university_name, major_name, program_name,
                   difficulty_label, course_evaluation_label, sentiment_label,
                   sentiment_score, created_at
            FROM posts 
            WHERE subreddit = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        
        return self.db_manager.execute_query(query, (subreddit, limit))
    
    def get_posts_by_university(self, university: str, limit: int = 20) -> List[Dict]:
        """Get posts mentioning specific university"""
        query = """
            SELECT post_id, subreddit, question_title, answer_content_cleaned,
                   major_name, program_name, difficulty_label, 
                   course_evaluation_label, sentiment_label, sentiment_score,
                   created_at
            FROM posts 
            WHERE university_name LIKE %s
            ORDER BY sentiment_score DESC, created_at DESC
            LIMIT %s
        """ if self.db_manager.db_type == 'mysql' else """
            SELECT post_id, subreddit, question_title, answer_content_cleaned,
                   major_name, program_name, difficulty_label, 
                   course_evaluation_label, sentiment_label, sentiment_score,
                   created_at
            FROM posts 
            WHERE university_name LIKE ?
            ORDER BY sentiment_score DESC, created_at DESC
            LIMIT ?
        """
        
        return self.db_manager.execute_query(query, (f'%{university}%', limit))
    
    def get_sentiment_analysis(self) -> Dict[str, Any]:
        """Get sentiment analysis statistics"""
        stats = {}
        
        # Overall sentiment distribution
        query = """
            SELECT sentiment_label, COUNT(*) as count, AVG(sentiment_score) as avg_score
            FROM posts 
            WHERE sentiment_label IS NOT NULL
            GROUP BY sentiment_label
            ORDER BY count DESC
        """
        stats['sentiment_distribution'] = self.db_manager.execute_query(query)
        
        # Sentiment by subreddit
        query = """
            SELECT subreddit, sentiment_label, COUNT(*) as count, AVG(sentiment_score) as avg_score
            FROM posts 
            WHERE sentiment_label IS NOT NULL
            GROUP BY subreddit, sentiment_label
            ORDER BY subreddit, count DESC
        """
        stats['sentiment_by_subreddit'] = self.db_manager.execute_query(query)
        
        # Top positive and negative posts
        query = """
            SELECT post_id, subreddit, question_title, sentiment_score, university_name
            FROM posts 
            WHERE sentiment_score IS NOT NULL
            ORDER BY sentiment_score DESC
            LIMIT 5
        """
        stats['most_positive'] = self.db_manager.execute_query(query)
        
        query = """
            SELECT post_id, subreddit, question_title, sentiment_score, university_name
            FROM posts 
            WHERE sentiment_score IS NOT NULL
            ORDER BY sentiment_score ASC
            LIMIT 5
        """
        stats['most_negative'] = self.db_manager.execute_query(query)
        
        return stats
    
    def get_difficulty_analysis(self) -> Dict[str, Any]:
        """Get application difficulty analysis"""
        stats = {}
        
        # Difficulty distribution
        query = """
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
                    ELSE 5
                END
        """
        stats['difficulty_distribution'] = self.db_manager.execute_query(query)
        
        # Difficulty by university
        query = """
            SELECT university_name, difficulty_label, COUNT(*) as count
            FROM posts 
            WHERE difficulty_label IS NOT NULL AND university_name IS NOT NULL AND university_name != ''
            GROUP BY university_name, difficulty_label
            HAVING count >= 2
            ORDER BY university_name, count DESC
        """
        stats['difficulty_by_university'] = self.db_manager.execute_query(query)
        
        return stats
    
    def get_university_rankings(self) -> List[Dict]:
        """Get university rankings based on sentiment and mentions"""
        query = """
            SELECT 
                university_name,
                COUNT(*) as mention_count,
                AVG(sentiment_score) as avg_sentiment,
                COUNT(CASE WHEN sentiment_label = '积极' THEN 1 END) as positive_count,
                COUNT(CASE WHEN sentiment_label = '消极' THEN 1 END) as negative_count,
                COUNT(CASE WHEN difficulty_label = '极难' THEN 1 END) as very_hard_count,
                COUNT(CASE WHEN difficulty_label = '难' THEN 1 END) as hard_count
            FROM posts 
            WHERE university_name IS NOT NULL AND university_name != ''
            GROUP BY university_name
            HAVING mention_count >= 3
            ORDER BY avg_sentiment DESC, mention_count DESC
            LIMIT 20
        """
        
        return self.db_manager.execute_query(query)
    
    def search_posts(self, keyword: str, limit: int = 20) -> List[Dict]:
        """Search posts by keyword in title or content"""
        query = """
            SELECT post_id, subreddit, question_title, answer_content_cleaned,
                   university_name, major_name, sentiment_label, sentiment_score,
                   created_at
            FROM posts 
            WHERE question_title LIKE %s OR answer_content_cleaned LIKE %s
            ORDER BY created_at DESC
            LIMIT %s
        """ if self.db_manager.db_type == 'mysql' else """
            SELECT post_id, subreddit, question_title, answer_content_cleaned,
                   university_name, major_name, sentiment_label, sentiment_score,
                   created_at
            FROM posts 
            WHERE question_title LIKE ? OR answer_content_cleaned LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        
        search_term = f'%{keyword}%'
        return self.db_manager.execute_query(query, (search_term, search_term, limit))
    
    def export_to_csv(self, filename: str, query: str = None) -> str:
        """Export data to CSV file"""
        if query is None:
            query = """
                SELECT post_id, subreddit, question_title, answer_content_cleaned,
                       university_name, major_name, program_name,
                       difficulty_label, course_evaluation_label, sentiment_label,
                       sentiment_score, created_at, processed_at
                FROM posts
                ORDER BY created_at DESC
            """
        
        data = self.db_manager.execute_query(query)
        
        if self.db_manager.db_type == 'sqlite':
            # Convert sqlite3.Row to dict
            data = [dict(row) for row in data]
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')
        
        log_message(f"Data exported to {filename}")
        return filename
    
    def get_processing_progress(self) -> Dict[str, Any]:
        """Get data processing progress"""
        stats = {}
        
        # Total posts
        result = self.db_manager.execute_query("SELECT COUNT(*) as count FROM posts")
        stats['total_posts'] = result[0]['count'] if self.db_manager.db_type == 'mysql' else result[0][0]
        
        # Processed posts
        result = self.db_manager.execute_query("SELECT COUNT(*) as count FROM posts WHERE processed_at IS NOT NULL")
        stats['processed_posts'] = result[0]['count'] if self.db_manager.db_type == 'mysql' else result[0][0]
        
        # Labeled posts
        result = self.db_manager.execute_query("SELECT COUNT(*) as count FROM posts WHERE sentiment_label IS NOT NULL")
        stats['labeled_posts'] = result[0]['count'] if self.db_manager.db_type == 'mysql' else result[0][0]
        
        # Posts with entities
        result = self.db_manager.execute_query("SELECT COUNT(*) as count FROM posts WHERE university_name IS NOT NULL AND university_name != ''")
        stats['posts_with_universities'] = result[0]['count'] if self.db_manager.db_type == 'mysql' else result[0][0]
        
        # Calculate percentages
        if stats['total_posts'] > 0:
            stats['processing_percentage'] = (stats['processed_posts'] / stats['total_posts']) * 100
            stats['labeling_percentage'] = (stats['labeled_posts'] / stats['total_posts']) * 100
            stats['entity_extraction_percentage'] = (stats['posts_with_universities'] / stats['total_posts']) * 100
        
        return stats
    
    def print_summary_report(self) -> None:
        """Print a comprehensive summary report"""
        print("=" * 80)
        print("REDDIT STUDY ABROAD DATA SCRAPER - SUMMARY REPORT")
        print("=" * 80)
        
        # Basic stats
        basic_stats = self.get_basic_stats()
        print(f"\n📊 BASIC STATISTICS:")
        print(f"  Total Posts: {basic_stats['total_posts']}")
        print(f"  Processed Posts: {basic_stats['processed_posts']}")
        print(f"  Labeled Posts: {basic_stats['labeled_posts']}")
        
        # Subreddit distribution
        print(f"\n📱 SUBREDDIT DISTRIBUTION:")
        for item in basic_stats['subreddit_distribution'][:10]:
            if self.db_manager.db_type == 'mysql':
                print(f"  r/{item['subreddit']}: {item['count']} posts")
            else:
                print(f"  r/{item[0]}: {item[1]} posts")
        
        # Processing progress
        progress = self.get_processing_progress()
        print(f"\n⚙️ PROCESSING PROGRESS:")
        print(f"  Processing: {progress.get('processing_percentage', 0):.1f}%")
        print(f"  Labeling: {progress.get('labeling_percentage', 0):.1f}%")
        print(f"  Entity Extraction: {progress.get('entity_extraction_percentage', 0):.1f}%")
        
        # Top universities
        universities = self.get_university_rankings()
        print(f"\n🏫 TOP UNIVERSITIES (by sentiment):")
        for i, uni in enumerate(universities[:10], 1):
            if self.db_manager.db_type == 'mysql':
                print(f"  {i}. {uni['university_name']}: {uni['avg_sentiment']:.1f}/10 ({uni['mention_count']} mentions)")
            else:
                print(f"  {i}. {uni[0]}: {uni[2]:.1f}/10 ({uni[1]} mentions)")
        
        print("=" * 80)
