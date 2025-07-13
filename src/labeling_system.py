"""
Labeling system for automatic content categorization
Implements Part 3 of the technical specification
"""

import re
import sqlite3
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import Counter
import json

from .utils import load_config, log_message
from .database_manager import create_database_manager


class LabelingSystem:
    """Automatic labeling system for Reddit study abroad posts"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the labeling system"""
        self.config = load_config(config_path)
        self.db_manager = create_database_manager(self.config)
        self.db_manager.connect()
        
        # Load label categories from config
        self.difficulty_labels = self.config['labeling']['difficulty_labels']
        self.course_labels = self.config['labeling']['course_evaluation_labels']
        self.sentiment_labels = self.config['labeling']['sentiment_labels']
        self.confidence_threshold = self.config['labeling']['confidence_threshold']
        
        # Initialize keyword dictionaries for rule-based labeling
        self._initialize_keywords()
    
    def _initialize_keywords(self):
        """Initialize keyword dictionaries for different label categories"""
        
        # Application difficulty keywords
        self.difficulty_keywords = {
            "极难": [
                "extremely difficult", "nearly impossible", "very competitive",
                "extremely competitive", "brutal", "cutthroat", "insane competition",
                "impossible to get in", "rejection rate", "top 1%"
            ],
            "难": [
                "difficult", "hard", "competitive", "challenging", "tough",
                "selective", "high standards", "rigorous", "demanding",
                "low acceptance rate", "hard to get in"
            ],
            "中等": [
                "moderate", "average", "decent chance", "reasonable",
                "fair competition", "standard requirements", "typical",
                "normal difficulty", "achievable"
            ],
            "易": [
                "easy", "simple", "not difficult", "straightforward",
                "high acceptance rate", "not competitive", "accessible",
                "easy to get in", "guaranteed admission"
            ]
        }
        
        # Course evaluation keywords
        self.course_keywords = {
            "优秀": [
                "excellent", "outstanding", "amazing", "fantastic", "brilliant",
                "top-notch", "world-class", "exceptional", "superb", "incredible",
                "highly recommend", "best course", "love this course"
            ],
            "良好": [
                "good", "great", "nice", "solid", "decent", "satisfactory",
                "recommend", "worth it", "helpful", "useful", "positive experience"
            ],
            "一般": [
                "okay", "average", "mediocre", "so-so", "nothing special",
                "typical", "standard", "neutral", "mixed feelings"
            ],
            "差": [
                "bad", "terrible", "awful", "horrible", "disappointing",
                "waste of time", "useless", "boring", "poorly taught",
                "don't recommend", "avoid", "regret taking"
            ]
        }
        
        # Sentiment keywords
        self.sentiment_keywords = {
            "积极": [
                "love", "enjoy", "happy", "excited", "grateful", "amazing",
                "wonderful", "fantastic", "great experience", "highly recommend",
                "positive", "satisfied", "thrilled", "blessed", "fortunate"
            ],
            "消极": [
                "hate", "disappointed", "frustrated", "regret", "terrible",
                "awful", "horrible", "nightmare", "stressed", "depressed",
                "negative", "dissatisfied", "angry", "upset", "worried"
            ],
            "中性": [
                "okay", "fine", "normal", "typical", "standard", "average",
                "neutral", "mixed", "uncertain", "undecided"
            ]
        }
    
    def calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """Calculate keyword-based score for text"""
        text_lower = text.lower()
        score = 0
        total_words = len(text_lower.split())
        
        for keyword in keywords:
            # Count occurrences of keyword
            count = text_lower.count(keyword.lower())
            # Weight by keyword importance (longer keywords get higher weight)
            weight = len(keyword.split())
            score += count * weight
        
        # Normalize by text length
        return score / max(total_words, 1)
    
    def classify_difficulty(self, text: str) -> Tuple[str, float]:
        """Classify application difficulty based on text content"""
        scores = {}
        
        for label, keywords in self.difficulty_keywords.items():
            scores[label] = self.calculate_keyword_score(text, keywords)
        
        # Find label with highest score
        best_label = max(scores, key=scores.get)
        confidence = scores[best_label]
        
        # Apply additional rules for better accuracy
        text_lower = text.lower()
        
        # Boost difficulty if specific indicators are present
        if any(indicator in text_lower for indicator in ["gpa 3.9", "gpa 4.0", "perfect score"]):
            if best_label in ["中等", "易"]:
                best_label = "难"
                confidence += 0.2
        
        # Boost ease if specific indicators are present
        if any(indicator in text_lower for indicator in ["guaranteed", "100% acceptance"]):
            best_label = "易"
            confidence += 0.3
        
        return best_label, min(confidence, 1.0)
    
    def classify_course_evaluation(self, text: str) -> Tuple[str, float]:
        """Classify course evaluation based on text content"""
        scores = {}
        
        for label, keywords in self.course_keywords.items():
            scores[label] = self.calculate_keyword_score(text, keywords)
        
        best_label = max(scores, key=scores.get)
        confidence = scores[best_label]
        
        # Apply contextual rules
        text_lower = text.lower()
        
        # Look for course-specific context
        course_indicators = ["professor", "class", "course", "lecture", "assignment", "exam"]
        has_course_context = any(indicator in text_lower for indicator in course_indicators)
        
        if not has_course_context:
            confidence *= 0.5  # Reduce confidence if no course context
        
        return best_label, min(confidence, 1.0)
    
    def classify_sentiment(self, text: str) -> Tuple[str, float]:
        """Classify sentiment based on text content"""
        scores = {}
        
        for label, keywords in self.sentiment_keywords.items():
            scores[label] = self.calculate_keyword_score(text, keywords)
        
        best_label = max(scores, key=scores.get)
        confidence = scores[best_label]
        
        # Apply sentiment-specific rules
        text_lower = text.lower()
        
        # Check for negation patterns
        negation_patterns = [
            r"not\s+\w+\s+(good|great|amazing|excellent)",
            r"don't\s+\w+\s+(like|love|enjoy)",
            r"never\s+\w+\s+(recommend|suggest)"
        ]
        
        for pattern in negation_patterns:
            if re.search(pattern, text_lower):
                if best_label == "积极":
                    best_label = "消极"
                    confidence += 0.2
        
        # Boost confidence for strong emotional indicators
        strong_positive = ["absolutely love", "highly recommend", "best decision"]
        strong_negative = ["worst experience", "complete disaster", "total waste"]
        
        if any(phrase in text_lower for phrase in strong_positive):
            best_label = "积极"
            confidence += 0.3
        elif any(phrase in text_lower for phrase in strong_negative):
            best_label = "消极"
            confidence += 0.3
        
        return best_label, min(confidence, 1.0)
    
    def calculate_sentiment_score(self, sentiment_label: str, confidence: float) -> float:
        """Convert sentiment label to numerical score (0-10)"""
        base_scores = {
            "消极": 2.0,
            "中性": 5.0,
            "积极": 8.0
        }
        
        base_score = base_scores.get(sentiment_label, 5.0)
        
        # Adjust based on confidence
        if sentiment_label == "积极":
            return base_score + (confidence * 2.0)  # 8-10 range
        elif sentiment_label == "消极":
            return base_score - (confidence * 2.0)  # 0-2 range
        else:
            return base_score  # Keep neutral at 5
    
    def label_post(self, post_id: int, text: str) -> Dict[str, any]:
        """Apply all labeling to a single post"""
        results = {}
        
        # Classify difficulty
        difficulty_label, difficulty_conf = self.classify_difficulty(text)
        results['difficulty_label'] = difficulty_label if difficulty_conf >= self.confidence_threshold else None
        results['difficulty_confidence'] = difficulty_conf
        
        # Classify course evaluation
        course_label, course_conf = self.classify_course_evaluation(text)
        results['course_label'] = course_label if course_conf >= self.confidence_threshold else None
        results['course_confidence'] = course_conf
        
        # Classify sentiment
        sentiment_label, sentiment_conf = self.classify_sentiment(text)
        results['sentiment_label'] = sentiment_label if sentiment_conf >= self.confidence_threshold else None
        results['sentiment_confidence'] = sentiment_conf
        results['sentiment_score'] = self.calculate_sentiment_score(sentiment_label, sentiment_conf)
        
        return results
    
    def label_all_posts(self) -> int:
        """Apply labeling to all processed posts in the database"""
        # Get all processed posts without labels
        query = """
            SELECT id, question_title, answer_content_cleaned, key_content
            FROM posts
            WHERE processed_at IS NOT NULL
            AND (difficulty_label IS NULL OR course_evaluation_label IS NULL OR sentiment_label IS NULL)
        """

        posts = self.db_manager.execute_query(query)
        labeled_count = 0

        log_message(f"Labeling {len(posts)} posts...")

        for post in posts:
            try:
                if self.db_manager.db_type == 'mysql':
                    post_id, title, content, key_content = post['id'], post['question_title'], post['answer_content_cleaned'], post['key_content']
                else:
                    post_id, title, content, key_content = post[0], post[1], post[2], post[3]

                # Combine all text for analysis
                combined_text = f"{title} {content} {key_content or ''}"

                # Apply labeling
                labels = self.label_post(post_id, combined_text)

                # Update database
                update_query = """
                    UPDATE posts SET
                        difficulty_label = %s,
                        course_evaluation_label = %s,
                        sentiment_label = %s,
                        sentiment_score = %s
                    WHERE id = %s
                """ if self.db_manager.db_type == 'mysql' else """
                    UPDATE posts SET
                        difficulty_label = ?,
                        course_evaluation_label = ?,
                        sentiment_label = ?,
                        sentiment_score = ?
                    WHERE id = ?
                """

                self.db_manager.execute_update(update_query, (
                    labels['difficulty_label'],
                    labels['course_label'],
                    labels['sentiment_label'],
                    labels['sentiment_score'],
                    post_id
                ))

                labeled_count += 1

                if labeled_count % 100 == 0:
                    log_message(f"Labeled {labeled_count}/{len(posts)} posts")

            except Exception as e:
                log_message(f"Error labeling post {post_id}: {e}", "ERROR")

        log_message(f"Completed labeling {labeled_count} posts")
        return labeled_count
    
    def get_labeling_stats(self) -> Dict[str, any]:
        """Get statistics about labeled data"""
        stats = {}

        # Total labeled posts
        result = self.db_manager.execute_query("""
            SELECT COUNT(*) as count FROM posts
            WHERE difficulty_label IS NOT NULL
            OR course_evaluation_label IS NOT NULL
            OR sentiment_label IS NOT NULL
        """)
        stats['total_labeled'] = result[0]['count'] if self.db_manager.db_type == 'mysql' else result[0][0]

        # Difficulty distribution
        result = self.db_manager.execute_query("SELECT difficulty_label, COUNT(*) as count FROM posts WHERE difficulty_label IS NOT NULL GROUP BY difficulty_label")
        if self.db_manager.db_type == 'mysql':
            stats['difficulty_distribution'] = {row['difficulty_label']: row['count'] for row in result}
        else:
            stats['difficulty_distribution'] = dict(result)

        # Course evaluation distribution
        result = self.db_manager.execute_query("SELECT course_evaluation_label, COUNT(*) as count FROM posts WHERE course_evaluation_label IS NOT NULL GROUP BY course_evaluation_label")
        if self.db_manager.db_type == 'mysql':
            stats['course_distribution'] = {row['course_evaluation_label']: row['count'] for row in result}
        else:
            stats['course_distribution'] = dict(result)

        # Sentiment distribution
        result = self.db_manager.execute_query("SELECT sentiment_label, COUNT(*) as count FROM posts WHERE sentiment_label IS NOT NULL GROUP BY sentiment_label")
        if self.db_manager.db_type == 'mysql':
            stats['sentiment_distribution'] = {row['sentiment_label']: row['count'] for row in result}
        else:
            stats['sentiment_distribution'] = dict(result)

        # Average sentiment score
        result = self.db_manager.execute_query("SELECT AVG(sentiment_score) as avg_score FROM posts WHERE sentiment_score IS NOT NULL")
        avg_sentiment = result[0]['avg_score'] if self.db_manager.db_type == 'mysql' else result[0][0]
        stats['average_sentiment_score'] = round(avg_sentiment, 2) if avg_sentiment else None

        return stats
