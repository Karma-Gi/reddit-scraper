"""
Database connection manager supporting both SQLite and MySQL
"""

import sqlite3
import mysql.connector
from mysql.connector import Error as MySQLError
from typing import Dict, Any, Optional, Union
import logging
from contextlib import contextmanager

from .utils import log_message


class DatabaseManager:
    """Database connection manager with support for SQLite and MySQL"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize database manager with configuration"""
        self.config = config
        self.db_type = config['database']['type'].lower()
        self.connection = None
        
        if self.db_type not in ['sqlite', 'mysql']:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def connect(self) -> Union[sqlite3.Connection, mysql.connector.MySQLConnection]:
        """Establish database connection"""
        try:
            if self.db_type == 'sqlite':
                self.connection = self._connect_sqlite()
            elif self.db_type == 'mysql':
                self.connection = self._connect_mysql()
            
            log_message(f"Connected to {self.db_type.upper()} database successfully")
            return self.connection
            
        except Exception as e:
            log_message(f"Failed to connect to {self.db_type} database: {e}", "ERROR")
            raise
    
    def _connect_sqlite(self) -> sqlite3.Connection:
        """Connect to SQLite database"""
        db_path = self.config['database']['sqlite']['name']
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def _connect_mysql(self) -> mysql.connector.MySQLConnection:
        """Connect to MySQL database"""
        mysql_config = self.config['database']['mysql']
        
        conn = mysql.connector.connect(
            host=mysql_config['host'],
            port=mysql_config['port'],
            database=mysql_config['database'],
            user=mysql_config['username'],
            password=mysql_config['password'],
            charset=mysql_config['charset'],
            autocommit=mysql_config.get('autocommit', True)
        )
        
        return conn
    
    def setup_tables(self) -> None:
        """Create database tables if they don't exist"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        
        try:
            if self.db_type == 'sqlite':
                self._create_sqlite_tables(cursor)
            elif self.db_type == 'mysql':
                self._create_mysql_tables(cursor)
            
            self.connection.commit()
            log_message("Database tables created successfully")
            
        except Exception as e:
            log_message(f"Error creating tables: {e}", "ERROR")
            raise
        finally:
            cursor.close()
    
    def _create_sqlite_tables(self, cursor) -> None:
        """Create SQLite tables"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT UNIQUE,
                subreddit TEXT,
                question_title TEXT,
                answer_content_raw TEXT,
                answer_content_cleaned TEXT,
                university_name TEXT,
                major_name TEXT,
                program_name TEXT,
                key_content TEXT,
                content_hash TEXT,
                difficulty_label TEXT,
                course_evaluation_label TEXT,
                sentiment_label TEXT,
                sentiment_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_content_hash ON posts(content_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_post_id ON posts(post_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_subreddit ON posts(subreddit)')
    
    def _create_mysql_tables(self, cursor) -> None:
        """Create MySQL tables"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                post_id VARCHAR(50) UNIQUE,
                subreddit VARCHAR(100),
                question_title TEXT,
                answer_content_raw LONGTEXT,
                answer_content_cleaned LONGTEXT,
                university_name TEXT,
                major_name TEXT,
                program_name TEXT,
                key_content TEXT,
                content_hash VARCHAR(32),
                difficulty_label VARCHAR(20),
                course_evaluation_label VARCHAR(20),
                sentiment_label VARCHAR(20),
                sentiment_score DECIMAL(3,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP NULL,
                INDEX idx_content_hash (content_hash),
                INDEX idx_post_id (post_id),
                INDEX idx_subreddit (subreddit),
                INDEX idx_difficulty (difficulty_label),
                INDEX idx_sentiment (sentiment_label)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            log_message(f"Database operation failed: {e}", "ERROR")
            raise
        finally:
            cursor.close()
    
    def execute_query(self, query: str, params: tuple = None) -> list:
        """Execute a SELECT query and return results"""
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if self.db_type == 'sqlite':
                return cursor.fetchall()
            else:  # MySQL
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount
    
    def execute_many(self, query: str, params_list: list) -> int:
        """Execute multiple queries with different parameters"""
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get information about the posts table"""
        info = {}
        
        # Get total record count
        result = self.execute_query("SELECT COUNT(*) as count FROM posts")
        info['total_posts'] = result[0]['count'] if self.db_type == 'mysql' else result[0][0]
        
        # Get subreddit distribution
        query = "SELECT subreddit, COUNT(*) as count FROM posts GROUP BY subreddit ORDER BY count DESC"
        info['subreddit_distribution'] = self.execute_query(query)
        
        # Get processing status
        query = "SELECT COUNT(*) as count FROM posts WHERE processed_at IS NOT NULL"
        result = self.execute_query(query)
        info['processed_posts'] = result[0]['count'] if self.db_type == 'mysql' else result[0][0]
        
        # Get labeling status
        query = "SELECT COUNT(*) as count FROM posts WHERE sentiment_label IS NOT NULL"
        result = self.execute_query(query)
        info['labeled_posts'] = result[0]['count'] if self.db_type == 'mysql' else result[0][0]
        
        return info
    
    def close(self) -> None:
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            log_message(f"Closed {self.db_type.upper()} database connection")


def create_database_manager(config: Dict[str, Any]) -> DatabaseManager:
    """Factory function to create database manager"""
    return DatabaseManager(config)
