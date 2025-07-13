"""
Unit tests for the labeling system module
"""

import unittest
import tempfile
import os
import sqlite3
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.labeling_system import LabelingSystem
from src.utils import setup_database


class TestLabelingSystem(unittest.TestCase):
    """Test cases for LabelingSystem class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        
        self.test_config = {
            'database': {'name': self.db_path},
            'labeling': {
                'difficulty_labels': ['极难', '难', '中等', '易'],
                'course_evaluation_labels': ['优秀', '良好', '一般', '差'],
                'sentiment_labels': ['积极', '消极', '中性'],
                'confidence_threshold': 0.7
            }
        }
        
        # Set up database with test data
        self.setup_test_database()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def setup_test_database(self):
        """Set up test database with sample data"""
        conn = setup_database(self.db_path)
        cursor = conn.cursor()
        
        # Insert test posts with processed content
        test_posts = [
            (1, "post1", "test", "MIT admission difficulty", 
             "MIT is extremely difficult to get into. Very competitive program.",
             "MIT is extremely difficult to get into. Very competitive program.",
             "MIT", "Computer Science", "PhD", 
             "MIT is extremely difficult and competitive", "hash1"),
            (2, "post2", "test", "Great course experience", 
             "This course was excellent! The professor was amazing and I learned so much.",
             "This course was excellent! The professor was amazing and I learned so much.",
             "Stanford", "Engineering", "MS", 
             "Course was excellent with amazing professor", "hash2"),
            (3, "post3", "test", "Mixed feelings about program", 
             "The program is okay, nothing special but not bad either.",
             "The program is okay, nothing special but not bad either.",
             "UC Berkeley", "Business", "MBA", 
             "Program is okay, nothing special", "hash3")
        ]
        
        cursor.executemany("""
            INSERT INTO posts (id, post_id, subreddit, question_title, answer_content_raw,
                             answer_content_cleaned, university_name, major_name, program_name,
                             key_content, content_hash) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, test_posts)
        
        # Mark posts as processed
        cursor.execute("UPDATE posts SET processed_at = CURRENT_TIMESTAMP")
        
        conn.commit()
        conn.close()
    
    def test_labeling_system_initialization(self):
        """Test labeling system initialization"""
        with unittest.mock.patch('src.labeling_system.load_config') as mock_config:
            mock_config.return_value = self.test_config
            labeler = LabelingSystem()
            
            self.assertEqual(labeler.config, self.test_config)
            self.assertEqual(labeler.db_path, self.db_path)
            self.assertEqual(labeler.difficulty_labels, ['极难', '难', '中等', '易'])
            self.assertIn("extremely difficult", labeler.difficulty_keywords["极难"])
    
    def test_calculate_keyword_score(self):
        """Test keyword scoring calculation"""
        with unittest.mock.patch('src.labeling_system.load_config') as mock_config:
            mock_config.return_value = self.test_config
            labeler = LabelingSystem()
            
            text = "This is extremely difficult and very competitive"
            keywords = ["extremely difficult", "competitive", "challenging"]
            
            score = labeler.calculate_keyword_score(text, keywords)
            
            # Should return a positive score for matching keywords
            self.assertGreater(score, 0)
            
            # Empty text should return 0
            empty_score = labeler.calculate_keyword_score("", keywords)
            self.assertEqual(empty_score, 0)
    
    def test_classify_difficulty(self):
        """Test difficulty classification"""
        with unittest.mock.patch('src.labeling_system.load_config') as mock_config:
            mock_config.return_value = self.test_config
            labeler = LabelingSystem()
            
            # Test extremely difficult text
            difficult_text = "MIT is extremely difficult and nearly impossible to get into"
            label, confidence = labeler.classify_difficulty(difficult_text)
            self.assertEqual(label, "极难")
            self.assertGreater(confidence, 0)
            
            # Test easy text
            easy_text = "This university has high acceptance rate and is easy to get into"
            label, confidence = labeler.classify_difficulty(easy_text)
            self.assertEqual(label, "易")
            self.assertGreater(confidence, 0)
            
            # Test moderate text
            moderate_text = "The admission requirements are reasonable and achievable"
            label, confidence = labeler.classify_difficulty(moderate_text)
            self.assertEqual(label, "中等")
    
    def test_classify_course_evaluation(self):
        """Test course evaluation classification"""
        with unittest.mock.patch('src.labeling_system.load_config') as mock_config:
            mock_config.return_value = self.test_config
            labeler = LabelingSystem()
            
            # Test excellent course
            excellent_text = "This course was excellent! The professor was amazing and I learned so much."
            label, confidence = labeler.classify_course_evaluation(excellent_text)
            self.assertEqual(label, "优秀")
            self.assertGreater(confidence, 0)
            
            # Test bad course
            bad_text = "This course was terrible and a waste of time. Don't recommend it."
            label, confidence = labeler.classify_course_evaluation(bad_text)
            self.assertEqual(label, "差")
            self.assertGreater(confidence, 0)
            
            # Test without course context (should have lower confidence)
            no_context_text = "This was excellent and amazing"
            label, confidence = labeler.classify_course_evaluation(no_context_text)
            # Confidence should be reduced due to lack of course context
            self.assertLess(confidence, 0.5)
    
    def test_classify_sentiment(self):
        """Test sentiment classification"""
        with unittest.mock.patch('src.labeling_system.load_config') as mock_config:
            mock_config.return_value = self.test_config
            labeler = LabelingSystem()
            
            # Test positive sentiment
            positive_text = "I absolutely love this university! Best decision ever!"
            label, confidence = labeler.classify_sentiment(positive_text)
            self.assertEqual(label, "积极")
            self.assertGreater(confidence, 0)
            
            # Test negative sentiment
            negative_text = "I hate this place. Worst experience of my life."
            label, confidence = labeler.classify_sentiment(negative_text)
            self.assertEqual(label, "消极")
            self.assertGreater(confidence, 0)
            
            # Test neutral sentiment
            neutral_text = "The program is okay, nothing special but not bad either."
            label, confidence = labeler.classify_sentiment(neutral_text)
            self.assertEqual(label, "中性")
    
    def test_calculate_sentiment_score(self):
        """Test sentiment score calculation"""
        with unittest.mock.patch('src.labeling_system.load_config') as mock_config:
            mock_config.return_value = self.test_config
            labeler = LabelingSystem()
            
            # Test positive sentiment score
            positive_score = labeler.calculate_sentiment_score("积极", 0.8)
            self.assertGreater(positive_score, 7)  # Should be in 8-10 range
            
            # Test negative sentiment score
            negative_score = labeler.calculate_sentiment_score("消极", 0.8)
            self.assertLess(negative_score, 3)  # Should be in 0-2 range
            
            # Test neutral sentiment score
            neutral_score = labeler.calculate_sentiment_score("中性", 0.5)
            self.assertEqual(neutral_score, 5.0)  # Should be exactly 5
    
    def test_label_post(self):
        """Test labeling a single post"""
        with unittest.mock.patch('src.labeling_system.load_config') as mock_config:
            mock_config.return_value = self.test_config
            labeler = LabelingSystem()
            
            test_text = "MIT is extremely difficult to get into. The course was excellent though!"
            results = labeler.label_post(1, test_text)
            
            # Should return all label types
            self.assertIn('difficulty_label', results)
            self.assertIn('course_label', results)
            self.assertIn('sentiment_label', results)
            self.assertIn('sentiment_score', results)
            
            # Should have confidence scores
            self.assertIn('difficulty_confidence', results)
            self.assertIn('course_confidence', results)
            self.assertIn('sentiment_confidence', results)
    
    def test_label_all_posts(self):
        """Test labeling all posts in database"""
        with unittest.mock.patch('src.labeling_system.load_config') as mock_config:
            mock_config.return_value = self.test_config
            labeler = LabelingSystem()
            
            labeled_count = labeler.label_all_posts()
            
            # Should label all test posts
            self.assertGreater(labeled_count, 0)
            
            # Check that posts have been labeled in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM posts 
                WHERE difficulty_label IS NOT NULL 
                OR course_evaluation_label IS NOT NULL 
                OR sentiment_label IS NOT NULL
            """)
            labeled_in_db = cursor.fetchone()[0]
            conn.close()
            
            self.assertGreater(labeled_in_db, 0)
    
    def test_get_labeling_stats(self):
        """Test getting labeling statistics"""
        with unittest.mock.patch('src.labeling_system.load_config') as mock_config:
            mock_config.return_value = self.test_config
            labeler = LabelingSystem()
            
            # Label posts first
            labeler.label_all_posts()
            
            stats = labeler.get_labeling_stats()
            
            # Should return valid statistics
            self.assertIn('total_labeled', stats)
            self.assertIn('difficulty_distribution', stats)
            self.assertIn('course_distribution', stats)
            self.assertIn('sentiment_distribution', stats)
            self.assertIn('average_sentiment_score', stats)
            
            self.assertGreater(stats['total_labeled'], 0)
            self.assertIsInstance(stats['difficulty_distribution'], dict)
            self.assertIsInstance(stats['course_distribution'], dict)
            self.assertIsInstance(stats['sentiment_distribution'], dict)
    
    def test_negation_handling(self):
        """Test handling of negation in sentiment analysis"""
        with unittest.mock.patch('src.labeling_system.load_config') as mock_config:
            mock_config.return_value = self.test_config
            labeler = LabelingSystem()
            
            # Test negated positive sentiment
            negated_text = "I don't really like this program at all"
            label, confidence = labeler.classify_sentiment(negated_text)
            
            # Should detect negative sentiment despite "like" keyword
            self.assertEqual(label, "消极")
    
    def test_confidence_threshold(self):
        """Test confidence threshold application"""
        with unittest.mock.patch('src.labeling_system.load_config') as mock_config:
            # Set high confidence threshold
            high_threshold_config = self.test_config.copy()
            high_threshold_config['labeling']['confidence_threshold'] = 0.9
            mock_config.return_value = high_threshold_config
            
            labeler = LabelingSystem()
            
            # Test with ambiguous text that should have low confidence
            ambiguous_text = "This is okay I guess"
            results = labeler.label_post(1, ambiguous_text)
            
            # With high threshold, labels might be None due to low confidence
            # At least some labels should be filtered out
            none_count = sum(1 for key in ['difficulty_label', 'course_label', 'sentiment_label'] 
                           if results[key] is None)
            self.assertGreater(none_count, 0)


if __name__ == '__main__':
    unittest.main()
