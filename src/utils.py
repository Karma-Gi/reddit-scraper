"""
Utility functions for the Reddit scraper project
"""

import random
import time
import yaml
import sqlite3
import hashlib
import re
from typing import List, Dict, Any, Optional
from pathlib import Path


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file {config_path} not found")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing configuration file: {e}")


# Removed get_random_user_agent - no longer needed for API scraping


def random_delay(min_delay: float, max_delay: float) -> None:
    """Sleep for a random duration between min_delay and max_delay seconds"""
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)


def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove special characters and normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    return text


def generate_content_hash(content: str) -> str:
    """Generate MD5 hash for content deduplication"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def setup_database(config: Dict[str, Any]):
    """Setup database with required tables using DatabaseManager"""
    from .database_manager import create_database_manager

    db_manager = create_database_manager(config)
    db_manager.connect()
    db_manager.setup_tables()
    return db_manager


def is_valid_content(content: str, min_length: int = 20, max_length: int = 5000) -> bool:
    """Check if content meets validity criteria"""
    if not content or not isinstance(content, str):
        return False
    
    content_length = len(content.strip())
    return min_length <= content_length <= max_length


def detect_language(text: str) -> str:
    """Detect language of text content with improved accuracy"""
    if not text or len(text.strip()) < 10:
        return "en"  # Assume short texts are English

    # Check for common English indicators first
    english_indicators = [
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'university', 'college', 'school', 'student', 'study', 'course', 'program',
        'application', 'admission', 'degree', 'major', 'gpa', 'sat', 'gre',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her'
    ]

    text_lower = text.lower()
    english_word_count = sum(1 for word in english_indicators if word in text_lower)

    # If we find many English indicators, assume it's English
    if english_word_count >= 3:
        return "en"

    # Try langdetect as fallback, but be more conservative
    try:
        from langdetect import detect, detect_langs

        # Get confidence scores
        langs = detect_langs(text)
        if langs:
            top_lang = langs[0]
            # Only trust the detection if confidence is high
            if top_lang.prob > 0.8:
                return top_lang.lang
            else:
                # Low confidence, check if English is in top candidates
                for lang in langs:
                    if lang.lang == 'en' and lang.prob > 0.3:
                        return "en"

        # Fallback to simple detection
        detected = detect(text)
        return detected if detected else "en"

    except Exception as e:
        # If langdetect fails or isn't installed, assume English
        # Most Reddit content in study abroad subreddits is English
        return "en"


def expand_abbreviations(text: str) -> str:
    """Expand common abbreviations in study abroad context"""
    abbreviations = {
        r'\buni\b': 'university',
        r'\bCS\b': 'Computer Science',
        r'\bEE\b': 'Electrical Engineering',
        r'\bME\b': 'Mechanical Engineering',
        r'\bCMU\b': 'Carnegie Mellon University',
        r'\bMIT\b': 'Massachusetts Institute of Technology',
        r'\bUC\b': 'University of California',
        r'\bGPA\b': 'Grade Point Average',
        r'\bGRE\b': 'Graduate Record Examination',
        r'\bTOEFL\b': 'Test of English as a Foreign Language',
        r'\bIELTS\b': 'International English Language Testing System'
    }
    
    for abbrev, full_form in abbreviations.items():
        text = re.sub(abbrev, full_form, text, flags=re.IGNORECASE)
    
    return text


def create_backup(db_path: str) -> str:
    """Create a backup of the database"""
    backup_path = f"{db_path}.backup_{int(time.time())}"
    
    # Copy database file
    import shutil
    shutil.copy2(db_path, backup_path)
    
    return backup_path


def log_message(message: str, level: str = "INFO") -> None:
    """Simple logging function"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")
