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
from .smart_entity_extractor import SmartEntityExtractor


class DataProcessor:
    """Data processor for cleaning and structuring scraped Reddit data"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the data processor"""
        self.config = load_config(config_path)
        self.db_manager = create_database_manager(self.config)
        self.db_manager.connect()
        
        # Load keywords from config (fallback)
        self.university_keywords = set(self.config['keywords']['universities'])
        self.major_keywords = set(self.config['keywords']['majors'])
        self.program_keywords = set(self.config['keywords']['programs'])

        # Initialize smart entity extractor
        self.smart_extractor = None
        if self.config.get('smart_extraction', {}).get('enabled', False):
            try:
                self.smart_extractor = SmartEntityExtractor(config_path)
                log_message("✅ Smart entity extractor initialized")
            except Exception as e:
                log_message(f"⚠️  Failed to initialize smart extractor: {e}", "WARNING")
                log_message("Falling back to keyword-based extraction")

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
        """Extract universities, majors, and programs from text using smart or fallback methods"""

        # Try smart extraction first
        if self.smart_extractor:
            try:
                entities = self.smart_extractor.extract_entities_smart(text)

                # Log extraction results for debugging
                total_entities = sum(len(v) for v in entities.values())
                if total_entities > 0:
                    log_message(f"Smart extraction found: {entities}")

                return entities

            except Exception as e:
                log_message(f"Smart extraction failed: {e}", "ERROR")
                log_message("Falling back to keyword extraction")

        # Fallback to keyword-based extraction
        return self._extract_entities_keyword(text)

    def _extract_entities_keyword(self, text: str) -> Dict[str, List[str]]:
        """Fallback keyword-based entity extraction"""
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
        # Get all posts with cleaned content
        query = """
            SELECT id, answer_content_cleaned
            FROM posts
            WHERE answer_content_cleaned IS NOT NULL
            AND LENGTH(answer_content_cleaned) > 50
        """

        posts = self.db_manager.execute_query(query)
        duplicates = []

        log_message(f"Checking {len(posts)} posts for duplicates...")

        # Compare each pair of posts
        for i in range(len(posts)):
            for j in range(i + 1, len(posts)):
                if self.db_manager.db_type == 'mysql':
                    id1, content1 = posts[i]['id'], posts[i]['answer_content_cleaned']
                    id2, content2 = posts[j]['id'], posts[j]['answer_content_cleaned']
                else:
                    id1, content1 = posts[i][0], posts[i][1]
                    id2, content2 = posts[j][0], posts[j][1]

                similarity = self.calculate_text_similarity(content1, content2)

                if similarity >= threshold:
                    duplicates.append((id1, id2, similarity))

        log_message(f"Found {len(duplicates)} duplicate pairs")
        return duplicates
    
    def remove_invalid_data(self) -> int:
        """Remove invalid, noise, and duplicate data"""
        removed_count = 0

        # First, check how many posts would be affected
        self._log_removal_preview()

        # Remove posts with invalid content length
        min_length = self.config['processing']['min_comment_length']
        max_length = self.config['processing']['max_comment_length']

        # Only remove posts that have been processed and have invalid length
        # Don't remove posts that haven't been processed yet (answer_content_cleaned is NULL)
        delete_query = """
            DELETE FROM posts
            WHERE answer_content_cleaned IS NOT NULL
            AND processed_at IS NOT NULL
            AND (LENGTH(answer_content_cleaned) < %s
                 OR LENGTH(answer_content_cleaned) > %s)
        """ if self.db_manager.db_type == 'mysql' else """
            DELETE FROM posts
            WHERE answer_content_cleaned IS NOT NULL
            AND processed_at IS NOT NULL
            AND (LENGTH(answer_content_cleaned) < ?
                 OR LENGTH(answer_content_cleaned) > ?)
        """

        count = self.db_manager.execute_update(delete_query, (min_length, max_length))
        removed_count += count
        log_message(f"Removed {count} posts with invalid length (min: {min_length}, max: {max_length})")

        # Remove non-English posts (if enabled and language detection is available)
        if self.config['processing'].get('enable_language_filter', False):
            try:
                target_lang = self.config['processing'].get('target_language', 'en')
                posts_query = "SELECT id, answer_content_cleaned FROM posts WHERE answer_content_cleaned IS NOT NULL AND processed_at IS NOT NULL"
                posts_to_check = self.db_manager.execute_query(posts_query)

                non_target_ids = []
                total_checked = 0

                log_message(f"Checking language for {len(posts_to_check)} posts (target: {target_lang})...")

                for post in posts_to_check:
                    if self.db_manager.db_type == 'mysql':
                        post_id, content = post['id'], post['answer_content_cleaned']
                    else:
                        post_id, content = post[0], post[1]

                    if content and len(content.strip()) > 10:  # Only check substantial content
                        detected_lang = detect_language(content)
                        total_checked += 1

                        if detected_lang != target_lang:
                            non_target_ids.append(post_id)
                            if len(non_target_ids) <= 5:  # Log first few for debugging
                                log_message(f"  Post {post_id}: detected as '{detected_lang}' - {content[:50]}...")

                log_message(f"Language detection results: {len(non_target_ids)}/{total_checked} posts detected as non-{target_lang}")

                if non_target_ids:
                    # Ask for confirmation if removing many posts
                    if len(non_target_ids) > len(posts_to_check) * 0.5:  # More than 50%
                        log_message(f"⚠️  WARNING: {len(non_target_ids)} posts ({len(non_target_ids)/len(posts_to_check)*100:.1f}%) detected as non-{target_lang}", "WARNING")
                        log_message("⚠️  This seems unusually high. Language detection might be inaccurate.", "WARNING")
                        log_message("⚠️  Consider setting 'enable_language_filter: false' in config.yaml", "WARNING")

                        # Don't auto-remove if detection seems inaccurate
                        if len(non_target_ids) > len(posts_to_check) * 0.8:  # More than 80%
                            log_message("⚠️  Skipping language filter due to suspicious results", "WARNING")
                            non_target_ids = []

                    if non_target_ids:
                        placeholders = ','.join(['%s'] * len(non_target_ids)) if self.db_manager.db_type == 'mysql' else ','.join(['?'] * len(non_target_ids))
                        delete_query = f"DELETE FROM posts WHERE id IN ({placeholders})"
                        count = self.db_manager.execute_update(delete_query, tuple(non_target_ids))
                        removed_count += count
                        log_message(f"Removed {count} non-{target_lang} posts")
                else:
                    log_message(f"All posts detected as {target_lang}")

            except Exception as e:
                log_message(f"Error in language detection: {e}", "ERROR")
                log_message("Skipping language filter due to error")
        else:
            log_message("Language filter disabled in configuration")

        # Remove duplicates
        duplicates = self.detect_duplicates(self.config['processing']['similarity_threshold'])
        duplicate_ids = [dup[1] for dup in duplicates]  # Keep first, remove second

        if duplicate_ids:
            placeholders = ','.join(['%s'] * len(duplicate_ids)) if self.db_manager.db_type == 'mysql' else ','.join(['?'] * len(duplicate_ids))
            delete_query = f"DELETE FROM posts WHERE id IN ({placeholders})"
            count = self.db_manager.execute_update(delete_query, tuple(duplicate_ids))
            removed_count += count
            log_message(f"Removed {count} duplicate posts")

        return removed_count

    def _log_removal_preview(self):
        """Log what would be removed before actually removing"""
        min_length = self.config['processing']['min_comment_length']
        max_length = self.config['processing']['max_comment_length']

        # Count total posts
        total_query = "SELECT COUNT(*) as count FROM posts"
        result = self.db_manager.execute_query(total_query)
        total_posts = result[0]['count'] if self.db_manager.db_type == 'mysql' else result[0][0]

        # Count processed posts
        processed_query = "SELECT COUNT(*) as count FROM posts WHERE processed_at IS NOT NULL"
        result = self.db_manager.execute_query(processed_query)
        processed_posts = result[0]['count'] if self.db_manager.db_type == 'mysql' else result[0][0]

        # Count posts that would be removed by length filter
        length_query = """
            SELECT COUNT(*) as count FROM posts
            WHERE answer_content_cleaned IS NOT NULL
            AND processed_at IS NOT NULL
            AND (LENGTH(answer_content_cleaned) < %s
                 OR LENGTH(answer_content_cleaned) > %s)
        """ if self.db_manager.db_type == 'mysql' else """
            SELECT COUNT(*) as count FROM posts
            WHERE answer_content_cleaned IS NOT NULL
            AND processed_at IS NOT NULL
            AND (LENGTH(answer_content_cleaned) < ?
                 OR LENGTH(answer_content_cleaned) > ?)
        """

        result = self.db_manager.execute_query(length_query, (min_length, max_length))
        would_remove = result[0]['count'] if self.db_manager.db_type == 'mysql' else result[0][0]

        log_message(f"Data removal preview:")
        log_message(f"  Total posts: {total_posts}")
        log_message(f"  Processed posts: {processed_posts}")
        log_message(f"  Posts that would be removed by length filter: {would_remove}")
        log_message(f"  Length criteria: {min_length} <= length <= {max_length}")

        if would_remove == processed_posts and processed_posts > 0:
            log_message("⚠️  WARNING: ALL processed posts would be removed!", "WARNING")
            log_message("⚠️  This suggests the length criteria are too strict!", "WARNING")
    
    def process_all_posts(self) -> int:
        """Process all posts in the database"""
        # Get all unprocessed posts
        query = """
            SELECT id, question_title, answer_content_raw
            FROM posts
            WHERE processed_at IS NULL
        """

        posts = self.db_manager.execute_query(query)
        processed_count = 0

        log_message(f"Processing {len(posts)} posts...")

        for post in posts:
            try:
                if self.db_manager.db_type == 'mysql':
                    post_id, title, raw_content = post['id'], post['question_title'], post['answer_content_raw']
                else:
                    post_id, title, raw_content = post[0], post[1], post[2]

                # Clean and normalize content
                cleaned_content = self.clean_and_normalize_text(raw_content)
                cleaned_title = self.clean_and_normalize_text(title)

                # Extract entities
                combined_text = f"{cleaned_title} {cleaned_content}"
                entities = self.extract_entities(combined_text)

                # Generate key content (simple extractive summary)
                key_content = self.extract_key_content(cleaned_content)

                # Update database
                update_query = """
                    UPDATE posts SET
                        answer_content_cleaned = %s,
                        university_name = %s,
                        major_name = %s,
                        program_name = %s,
                        key_content = %s,
                        processed_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """ if self.db_manager.db_type == 'mysql' else """
                    UPDATE posts SET
                        answer_content_cleaned = ?,
                        university_name = ?,
                        major_name = ?,
                        program_name = ?,
                        key_content = ?,
                        processed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """

                self.db_manager.execute_update(update_query, (
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

            except Exception as e:
                log_message(f"Error processing post {post_id}: {e}", "ERROR")

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
        stats = {}

        # Total posts
        result = self.db_manager.execute_query("SELECT COUNT(*) as count FROM posts")
        stats['total_posts'] = result[0]['count'] if self.db_manager.db_type == 'mysql' else result[0][0]

        # Processed posts
        result = self.db_manager.execute_query("SELECT COUNT(*) as count FROM posts WHERE processed_at IS NOT NULL")
        stats['processed_posts'] = result[0]['count'] if self.db_manager.db_type == 'mysql' else result[0][0]

        # Posts with entities
        result = self.db_manager.execute_query("SELECT COUNT(*) as count FROM posts WHERE university_name != '' AND university_name IS NOT NULL")
        stats['posts_with_universities'] = result[0]['count'] if self.db_manager.db_type == 'mysql' else result[0][0]

        result = self.db_manager.execute_query("SELECT COUNT(*) as count FROM posts WHERE major_name != '' AND major_name IS NOT NULL")
        stats['posts_with_majors'] = result[0]['count'] if self.db_manager.db_type == 'mysql' else result[0][0]

        result = self.db_manager.execute_query("SELECT COUNT(*) as count FROM posts WHERE program_name != '' AND program_name IS NOT NULL")
        stats['posts_with_programs'] = result[0]['count'] if self.db_manager.db_type == 'mysql' else result[0][0]

        return stats
