#!/usr/bin/env python3
"""
MySQL database setup script for Reddit Study Abroad Scraper
"""

import mysql.connector
from mysql.connector import Error as MySQLError
import yaml
import sys
import getpass


def load_config(config_path: str = "config.yaml"):
    """Load configuration from YAML file"""
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


def create_database_and_user(config):
    """Create MySQL database and user if they don't exist"""
    mysql_config = config['database']['mysql']
    
    # Connect as root to create database and user
    root_password = getpass.getpass("Enter MySQL root password: ")
    
    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(
            host=mysql_config['host'],
            port=mysql_config['port'],
            user='root',
            password=root_password
        )
        
        cursor = connection.cursor()
        
        # Create database
        database_name = mysql_config['database']
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✅ Database '{database_name}' created successfully")
        
        # Create user (if not root)
        username = mysql_config['username']
        user_password = mysql_config['password']
        
        if username != 'root':
            # Drop user if exists (to handle password changes)
            cursor.execute(f"DROP USER IF EXISTS '{username}'@'%'")
            
            # Create user
            cursor.execute(f"CREATE USER '{username}'@'%' IDENTIFIED BY '{user_password}'")
            
            # Grant privileges
            cursor.execute(f"GRANT ALL PRIVILEGES ON {database_name}.* TO '{username}'@'%'")
            cursor.execute("FLUSH PRIVILEGES")
            
            print(f"✅ User '{username}' created with full privileges on '{database_name}'")
        
        cursor.close()
        connection.close()
        
        return True
        
    except MySQLError as e:
        print(f"❌ MySQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_connection(config):
    """Test connection to the configured database"""
    mysql_config = config['database']['mysql']
    
    try:
        connection = mysql.connector.connect(
            host=mysql_config['host'],
            port=mysql_config['port'],
            database=mysql_config['database'],
            user=mysql_config['username'],
            password=mysql_config['password'],
            charset=mysql_config['charset']
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        
        print(f"✅ Successfully connected to MySQL {version[0]}")
        print(f"   Database: {mysql_config['database']}")
        print(f"   Host: {mysql_config['host']}:{mysql_config['port']}")
        print(f"   User: {mysql_config['username']}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except MySQLError as e:
        print(f"❌ Connection failed: {e}")
        return False


def create_tables(config):
    """Create the required tables in the database"""
    try:
        from src.database_manager import create_database_manager
        
        db_manager = create_database_manager(config)
        db_manager.connect()
        db_manager.setup_tables()
        db_manager.close()
        
        print("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False


def main():
    """Main setup function"""
    print("=" * 60)
    print("MYSQL DATABASE SETUP FOR REDDIT SCRAPER")
    print("=" * 60)
    
    try:
        # Load configuration
        config = load_config()
        
        if config['database']['type'].lower() != 'mysql':
            print("❌ Database type is not set to 'mysql' in config.yaml")
            print("   Please update the 'database.type' setting to 'mysql'")
            sys.exit(1)
        
        print("Current MySQL configuration:")
        mysql_config = config['database']['mysql']
        print(f"  Host: {mysql_config['host']}:{mysql_config['port']}")
        print(f"  Database: {mysql_config['database']}")
        print(f"  Username: {mysql_config['username']}")
        print(f"  Charset: {mysql_config['charset']}")
        
        # Ask for confirmation
        response = input("\nProceed with setup? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            sys.exit(0)
        
        # Step 1: Create database and user
        print("\n📝 Step 1: Creating database and user...")
        if not create_database_and_user(config):
            print("❌ Failed to create database and user")
            sys.exit(1)
        
        # Step 2: Test connection
        print("\n🔗 Step 2: Testing connection...")
        if not test_connection(config):
            print("❌ Connection test failed")
            sys.exit(1)
        
        # Step 3: Create tables
        print("\n🗃️ Step 3: Creating tables...")
        if not create_tables(config):
            print("❌ Failed to create tables")
            sys.exit(1)
        
        print("\n" + "=" * 60)
        print("✅ MYSQL SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nYou can now run the scraper with MySQL:")
        print("  python main.py --full")
        print("  python main.py --view")
        print("  python main.py --stats")
        
    except FileNotFoundError:
        print("❌ config.yaml not found. Please ensure the configuration file exists.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
