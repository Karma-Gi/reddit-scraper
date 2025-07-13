"""
Unit tests for the data processor module
"""

import unittest
import tempfile
import os
import sqlite3
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.data_processor import DataProcessor
from src.utils import setup_database


class TestDataProcessor(unittest.TestCase):
    """Test cases for DataProcessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        
        self.test_config = {
            'database': {'name': self.db_path},
            'processing': {
                'min_comment_length': 20,
                'max_comment_length': 5000,
                'similarity_threshold': 0.85
            },
            'keywords': {
                'universities': ['MIT', 'Stanford', 'Harvard', 'CMU'],
                'majors': ['Computer Science', 'Engineering', 'Medicine'],
                'programs': ['PhD', 'Master', 'BS', 'MS']
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
        
        # Insert test posts
        test_posts = [
            (1, "post1", "test", "How to get into MIT?", 
             "I want to apply to MIT for Computer Science PhD program. Any advice?",
             None, None, None, None, None, "hash1"),
            (2, "post2", "test", "Stanford admission", 
             "Stanford is very competitive for Engineering. I got rejected.",
             None, None, None, None, None, "hash2"),
            (3, "post3", "test", "Short post", "Too short",
             None, None, None, None, None, "hash3"),
            (4, "post4", "test", "Duplicate content test",
             "I want to apply to MIT for Computer Science PhD program. Any advice?",
             None, None, None, None, None, "hash4")
        ]
        
        cursor.executemany("""
            INSERT INTO posts (id, post_id, subreddit, question_title, answer_content_raw,
                             answer_content_cleaned, university_name, major_name, program_name,
                             key_content, content_hash) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, test_posts)
        
        conn.commit()
        conn.close()
    
    def test_processor_initialization(self):
        """Test processor initialization"""
        with unittest.mock.patch('src.data_processor.load_config') as mock_config:
            mock_config.return_value = self.test_config
            processor = DataProcessor()
            
            self.assertEqual(processor.config, self.test_config)
            self.assertEqual(processor.db_path, self.db_path)
            self.assertIn('MIT', processor.university_keywords)
    
    def test_clean_and_normalize_text(self):
        """Test text cleaning and normalization"""
        with unittest.mock.patch('src.data_processor.load_config') as mock_config:
            mock_config.return_value = self.test_config
            processor = DataProcessor()
            
            # Test various text cleaning scenarios
            dirty_text = "  Check out this link: https://example.com  and email me at test@example.com!!! "
            clean_text = processor.clean_and_normalize_text(dirty_text)
            
            self.assertNotIn("https://example.com", clean_text)
            self.assertNotIn("test@example.com", clean_text)
            self.assertNotIn("!!!", clean_text)
            self.assertEqual(clean_text.strip(), clean_text)  # No leading/trailing spaces
    
    def test_extract_entities(self):
        """Test entity extraction from text"""
        with unittest.mock.patch('src.data_processor.load_config') as mock_config:
            mock_config.return_value = self.test_config
            processor = DataProcessor()
            
            test_text = "I'm applying to MIT and Stanford for Computer Science PhD program"
            entities = processor.extract_entities(test_text)
            
            self.assertIn('MIT', entities['universities'])
            self.assertIn('Stanford', entities['universities'])
            self.assertIn('Computer Science', entities['majors'])
            self.assertIn('PhD', entities['programs'])
    
    def test_calculate_text_similarity(self):
        """Test text similarity calculation"""
        with unittest.mock.patch('src.data_processor.load_config') as mock_config:
            mock_config.return_value = self.test_config
            processor = DataProcessor()
            
            text1 = "I want to apply to MIT for Computer Science"
            text2 = "I want to apply to MIT for Computer Science"
            text3 = "Stanford is a great university for engineering"
            
            # Identical texts should have similarity of 1.0
            similarity1 = processor.calculate_text_similarity(text1, text2)
            self.assertEqual(similarity1, 1.0)
            
            # Different texts should have lower similarity
            similarity2 = processor.calculate_text_similarity(text1, text3)
            self.assertLess(similarity2, 0.5)
    
    def test_detect_duplicates(self):
        """Test duplicate detection"""
        with unittest.mock.patch('src.data_processor.load_config') as mock_config:
            mock_config.return_value = self.test_config
            processor = DataProcessor()
            
            # First, process the posts to add cleaned content
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE posts SET answer_content_cleaned = answer_content_raw 
                WHERE answer_content_cleaned IS NULL
            """)
            conn.commit()
            conn.close()
            
            duplicates = processor.detect_duplicates(threshold=0.8)
            
            # Should detect the duplicate posts (post1 and post4 have similar content)
            self.assertGreater(len(duplicates), 0)
    
    def test_remove_invalid_data(self):
        """Test removal of invalid data"""
        with unittest.mock.patch('src.data_processor.load_config') as mock_config:
            mock_config.return_value = self.test_config
            processor = DataProcessor()
            
            # First, add cleaned content
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE posts SET answer_content_cleaned = answer_content_raw 
                WHERE answer_content_cleaned IS NULL
            """)
            conn.commit()
            
            # Count posts before removal
            cursor.execute("SELECT COUNT(*) FROM posts")
            count_before = cursor.fetchone()[0]
            conn.close()
            
            # Remove invalid data
            removed_count = processor.remove_invalid_data()
            
            # Count posts after removal
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM posts")
            count_after = cursor.fetchone()[0]
            conn.close()
            
            # Should have removed at least the short post
            self.assertGreater(removed_count, 0)
            self.assertLess(count_after, count_before)
    
    def test_extract_key_content(self):
        """Test key content extraction"""
        with unittest.mock.patch('src.data_processor.load_config') as mock_config:
            mock_config.return_value = self.test_config
            processor = DataProcessor()
            
            long_text = """
            I applied to MIT for Computer Science PhD program last year. 
            The application process was very competitive and difficult. 
            I had a GPA of 3.8 and good research experience. 
            The interview was challenging but fair. 
            I would recommend preparing well for the technical questions.
            Overall, it was a great experience despite the stress.
            """
            
            key_content = processor.extract_key_content(long_text, max_sentences=2)
            
            # Should return a shorter version
            self.assertLess(len(key_content), len(long_text))
            self.assertGreater(len(key_content), 0)
            
            # Should contain important keywords
            key_content_lower = key_content.lower()
            self.assertTrue(any(keyword in key_content_lower 
                              for keyword in ['mit', 'computer science', 'application', 'recommend']))
    
    def test_process_all_posts(self):
        """Test processing all posts"""
        with unittest.mock.patch('src.data_processor.load_config') as mock_config:
            mock_config.return_value = self.test_config
            processor = DataProcessor()
            
            processed_count = processor.process_all_posts()
            
            # Should process all posts
            self.assertGreater(processed_count, 0)
            
            # Check that processed posts have cleaned content
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM posts 
                WHERE processed_at IS NOT NULL AND answer_content_cleaned IS NOT NULL
            """)
            processed_in_db = cursor.fetchone()[0]
            conn.close()
            
            self.assertEqual(processed_count, processed_in_db)
    
    def test_get_processing_stats(self):
        """Test getting processing statistics"""
        with unittest.mock.patch('src.data_processor.load_config') as mock_config:
            mock_config.return_value = self.test_config
            processor = DataProcessor()
            
            # Process some posts first
            processor.process_all_posts()
            
            stats = processor.get_processing_stats()
            
            # Should return valid statistics
            self.assertIn('total_posts', stats)
            self.assertIn('processed_posts', stats)
            self.assertIn('posts_with_universities', stats)
            self.assertIn('posts_with_majors', stats)
            self.assertIn('posts_with_programs', stats)
            
            self.assertGreater(stats['total_posts'], 0)
            self.assertGreater(stats['processed_posts'], 0)


if __name__ == '__main__':
    unittest.main()
