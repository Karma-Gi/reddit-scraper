"""
Data processing and cleaning module
Implements Part 2 of the technical specification
"""

import re
import sqlite3
import pandas as pd
import numpy as np
from typing import List, Dict, Set, Tuple, Optional
from collections import Counter
import hashlib
from difflib import SequenceMatcher

from .utils import (
    load_config, clean_text, expand_abbreviations,
    is_valid_content, detect_language, log_message
)
from .database_manager import create_database_manager


class DataProcessor:
    """Data processor for cleaning and structuring scraped Reddit data"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the data processor"""
        self.config = load_config(config_path)
        self.db_manager = create_database_manager(self.config)
        self.db_manager.connect()
        
        # Load keywords from config
        self.university_keywords = set(self.config['keywords']['universities'])
        self.major_keywords = set(self.config['keywords']['majors'])
        self.program_keywords = set(self.config['keywords']['programs'])
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for text processing"""
        # Pattern for removing URLs
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        # Pattern for removing email addresses
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Pattern for removing excessive whitespace
        self.whitespace_pattern = re.compile(r'\s+')
        
        # Pattern for removing special characters (keep basic punctuation)
        self.special_char_pattern = re.compile(r'[^\w\s.,!?;:()\-\'\"]+')
    
    def clean_and_normalize_text(self, text: str) -> str:
        """Advanced text cleaning and normalization"""
        if not text:
            return ""
        
        # Remove URLs and email addresses
        text = self.url_pattern.sub('', text)
        text = self.email_pattern.sub('', text)
        
        # Remove HTML entities
        text = re.sub(r'&[a-zA-Z0-9#]+;', '', text)
        
        # Expand abbreviations
        text = expand_abbreviations(text)
        
        # Remove excessive special characters
        text = self.special_char_pattern.sub(' ', text)
        
        # Normalize whitespace
        text = self.whitespace_pattern.sub(' ', text)
        
        # Remove extra punctuation
        text = re.sub(r'[.]{2,}', '.', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        return text.strip()
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract universities, majors, and programs from text"""
        text_lower = text.lower()
        entities = {
            'universities': [],
            'majors': [],
            'programs': []
        }
        
        # Extract universities
        for university in self.university_keywords:
            if university.lower() in text_lower:
                entities['universities'].append(university)
        
        # Extract majors
        for major in self.major_keywords:
            if major.lower() in text_lower:
                entities['majors'].append(major)
        
        # Extract programs
        for program in self.program_keywords:
            if program.lower() in text_lower:
                entities['programs'].append(program)
        
        # Use regex for more complex patterns
        # University patterns
        university_patterns = [
            r'\b([A-Z][a-z]+ (?:University|Institute|College))\b',
            r'\b(University of [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            r'\b([A-Z]{2,5})\b(?=.*(?:university|college|institute))',
        ]
        
        for pattern in university_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['universities'].extend(matches)
        
        # Remove duplicates and clean
        for key in entities:
            entities[key] = list(set([item.strip() for item in entities[key] if item.strip()]))
        
        return entities
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using SequenceMatcher"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def detect_duplicates(self, threshold: float = 0.85) -> List[Tuple[int, int, float]]:
        """Detect duplicate or highly similar posts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all posts with cleaned content
        cursor.execute("""
            SELECT id, answer_content_cleaned 
            FROM posts 
            WHERE answer_content_cleaned IS NOT NULL 
            AND LENGTH(answer_content_cleaned) > 50
        """)
        
        posts = cursor.fetchall()
        duplicates = []
        
        log_message(f"Checking {len(posts)} posts for duplicates...")
        
        # Compare each pair of posts
        for i in range(len(posts)):
            for j in range(i + 1, len(posts)):
                id1, content1 = posts[i]
                id2, content2 = posts[j]
                
                similarity = self.calculate_text_similarity(content1, content2)
                
                if similarity >= threshold:
                    duplicates.append((id1, id2, similarity))
        
        conn.close()
        log_message(f"Found {len(duplicates)} duplicate pairs")
        return duplicates
    
    def remove_invalid_data(self) -> int:
        """Remove invalid, noise, and duplicate data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        removed_count = 0
        
        # Remove posts with invalid content length
        min_length = self.config['processing']['min_comment_length']
        max_length = self.config['processing']['max_comment_length']
        
        cursor.execute("""
            DELETE FROM posts 
            WHERE LENGTH(answer_content_cleaned) < ? 
            OR LENGTH(answer_content_cleaned) > ?
        """, (min_length, max_length))
        
        removed_count += cursor.rowcount
        log_message(f"Removed {cursor.rowcount} posts with invalid length")
        
        # Remove non-English posts (if language detection is available)
        try:
            cursor.execute("SELECT id, answer_content_cleaned FROM posts")
            posts_to_check = cursor.fetchall()
            
            non_english_ids = []
            for post_id, content in posts_to_check:
                if detect_language(content) != 'en':
                    non_english_ids.append(post_id)
            
            if non_english_ids:
                placeholders = ','.join(['?'] * len(non_english_ids))
                cursor.execute(f"DELETE FROM posts WHERE id IN ({placeholders})", non_english_ids)
                removed_count += cursor.rowcount
                log_message(f"Removed {cursor.rowcount} non-English posts")
                
        except ImportError:
            log_message("Language detection not available, skipping language filter")
        
        # Remove duplicates
        duplicates = self.detect_duplicates(self.config['processing']['similarity_threshold'])
        duplicate_ids = [dup[1] for dup in duplicates]  # Keep first, remove second
        
        if duplicate_ids:
            placeholders = ','.join(['?'] * len(duplicate_ids))
            cursor.execute(f"DELETE FROM posts WHERE id IN ({placeholders})", duplicate_ids)
            removed_count += cursor.rowcount
            log_message(f"Removed {cursor.rowcount} duplicate posts")
        
        conn.commit()
        conn.close()
        
        return removed_count
    
    def process_all_posts(self) -> int:
        """Process all posts in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all unprocessed posts
        cursor.execute("""
            SELECT id, question_title, answer_content_raw 
            FROM posts 
            WHERE processed_at IS NULL
        """)
        
        posts = cursor.fetchall()
        processed_count = 0
        
        log_message(f"Processing {len(posts)} posts...")
        
        for post_id, title, raw_content in posts:
            try:
                # Clean and normalize content
                cleaned_content = self.clean_and_normalize_text(raw_content)
                cleaned_title = self.clean_and_normalize_text(title)
                
                # Extract entities
                combined_text = f"{cleaned_title} {cleaned_content}"
                entities = self.extract_entities(combined_text)
                
                # Generate key content (simple extractive summary)
                key_content = self.extract_key_content(cleaned_content)
                
                # Update database
                cursor.execute("""
                    UPDATE posts SET 
                        answer_content_cleaned = ?,
                        university_name = ?,
                        major_name = ?,
                        program_name = ?,
                        key_content = ?,
                        processed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    cleaned_content,
                    ', '.join(entities['universities'][:3]),  # Limit to top 3
                    ', '.join(entities['majors'][:3]),
                    ', '.join(entities['programs'][:3]),
                    key_content,
                    post_id
                ))
                
                processed_count += 1
                
                if processed_count % 100 == 0:
                    log_message(f"Processed {processed_count}/{len(posts)} posts")
                    conn.commit()
                    
            except Exception as e:
                log_message(f"Error processing post {post_id}: {e}", "ERROR")
        
        conn.commit()
        conn.close()
        
        log_message(f"Completed processing {processed_count} posts")
        return processed_count
    
    def extract_key_content(self, text: str, max_sentences: int = 3) -> str:
        """Extract key content from text using simple sentence ranking"""
        if not text:
            return ""
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if len(sentences) <= max_sentences:
            return '. '.join(sentences)
        
        # Simple scoring based on keyword presence and sentence length
        scored_sentences = []
        
        for sentence in sentences:
            score = 0
            sentence_lower = sentence.lower()
            
            # Score based on keyword presence
            keywords = ['university', 'college', 'admission', 'application', 'gpa', 
                       'experience', 'recommend', 'difficult', 'easy', 'good', 'bad']
            
            for keyword in keywords:
                if keyword in sentence_lower:
                    score += 1
            
            # Prefer medium-length sentences
            length_score = min(len(sentence) / 100, 1.0)
            score += length_score
            
            scored_sentences.append((sentence, score))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in scored_sentences[:max_sentences]]
        
        return '. '.join(top_sentences)
    
    def get_processing_stats(self) -> Dict[str, int]:
        """Get statistics about processed data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total posts
        cursor.execute("SELECT COUNT(*) FROM posts")
        stats['total_posts'] = cursor.fetchone()[0]
        
        # Processed posts
        cursor.execute("SELECT COUNT(*) FROM posts WHERE processed_at IS NOT NULL")
        stats['processed_posts'] = cursor.fetchone()[0]
        
        # Posts with entities
        cursor.execute("SELECT COUNT(*) FROM posts WHERE university_name != ''")
        stats['posts_with_universities'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM posts WHERE major_name != ''")
        stats['posts_with_majors'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM posts WHERE program_name != ''")
        stats['posts_with_programs'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
