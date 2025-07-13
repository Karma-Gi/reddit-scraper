#!/usr/bin/env python3
"""
Reddit API setup script
Guides user through Reddit app registration and configuration
"""

import yaml
import sys
import webbrowser
from pathlib import Path


def print_header():
    """Print setup header"""
    print("🔧 REDDIT API SETUP WIZARD")
    print("=" * 50)
    print("This script will help you set up Reddit API access for the scraper.")
    print("Reddit API is more reliable and faster than web scraping!")
    print()


def open_reddit_apps_page():
    """Open Reddit apps page in browser"""
    print("📱 STEP 1: CREATE REDDIT APP")
    print("-" * 30)
    print("We need to create a Reddit application to get API credentials.")
    print()
    
    response = input("Open Reddit apps page in browser? (Y/n): ").strip().lower()
    if response != 'n':
        webbrowser.open("https://www.reddit.com/prefs/apps/")
        print("✅ Opened https://www.reddit.com/prefs/apps/ in your browser")
    else:
        print("📋 Please manually visit: https://www.reddit.com/prefs/apps/")
    
    print()
    print("📝 Instructions:")
    print("1. Log in to your Reddit account")
    print("2. Scroll down and click 'Create App' or 'Create Another App'")
    print("3. Fill in the form:")
    print("   • Name: StudyAbroadScraper")
    print("   • App type: Select 'script'")
    print("   • Description: Data scraper for study abroad discussions")
    print("   • About URL: (leave blank)")
    print("   • Redirect URI: http://localhost:8080")
    print("4. Click 'Create app'")
    print()
    
    input("Press Enter when you've created the app...")


def get_api_credentials():
    """Get API credentials from user"""
    print("🔑 STEP 2: GET API CREDENTIALS")
    print("-" * 30)
    print("After creating the app, you should see:")
    print("• A string under the app name (this is your CLIENT_ID)")
    print("• A 'secret' field (this is your CLIENT_SECRET)")
    print()
    
    client_id = input("Enter your CLIENT_ID: ").strip()
    if not client_id:
        print("❌ Client ID is required!")
        return None, None
    
    client_secret = input("Enter your CLIENT_SECRET: ").strip()
    if not client_secret:
        print("❌ Client secret is required!")
        return None, None
    
    print("✅ Credentials received!")
    return client_id, client_secret


def get_optional_credentials():
    """Get optional username/password for authenticated access"""
    print("\n🔐 STEP 3: OPTIONAL AUTHENTICATION")
    print("-" * 30)
    print("You can optionally provide your Reddit username and password")
    print("for authenticated access (allows access to more data).")
    print("This is optional - you can skip this step.")
    print()
    
    response = input("Do you want to add Reddit username/password? (y/N): ").strip().lower()
    if response == 'y':
        username = input("Reddit username: ").strip()
        password = input("Reddit password: ").strip()
        return username, password
    
    return "", ""


def update_config_file(client_id, client_secret, username="", password=""):
    """Update config.yaml with Reddit API credentials"""
    config_path = "config.yaml"
    
    try:
        # Load existing config
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        
        # Update Reddit API settings
        config['reddit_api'] = {
            'client_id': client_id,
            'client_secret': client_secret,
            'user_agent': 'StudyAbroadScraper/1.0 by RedditUser',
            'username': username,
            'password': password
        }
        
        # Set scraping method to API
        config['scraping']['method'] = 'api'
        
        # Save updated config
        with open(config_path, 'w', encoding='utf-8') as file:
            yaml.dump(config, file, default_flow_style=False, allow_unicode=True)
        
        print(f"✅ Updated {config_path} with Reddit API credentials")
        return True
        
    except Exception as e:
        print(f"❌ Error updating config file: {e}")
        return False


def test_api_connection():
    """Test Reddit API connection"""
    print("\n🧪 STEP 4: TEST API CONNECTION")
    print("-" * 30)
    
    try:
        # Import and test
        from src.reddit_api_scraper import test_reddit_api_connection
        
        print("Testing Reddit API connection...")
        if test_reddit_api_connection():
            print("✅ Reddit API connection successful!")
            return True
        else:
            print("❌ Reddit API connection failed!")
            return False
            
    except ImportError:
        print("⚠️  Cannot test connection - PRAW not installed")
        print("   Run: pip install praw")
        return False
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False


def show_next_steps():
    """Show next steps after setup"""
    print("\n🎉 SETUP COMPLETE!")
    print("=" * 30)
    print("Your Reddit API scraper is now configured!")
    print()
    print("📋 Next steps:")
    print("1. Install PRAW if not already installed:")
    print("   pip install praw")
    print()
    print("2. Run the scraper:")
    print("   python main.py --full")
    print()
    print("3. View scraped data:")
    print("   python main.py --view")
    print("   python main.py --stats")
    print()
    print("4. Export data:")
    print("   python main.py --export data.csv")
    print()
    print("🔧 Configuration:")
    print("• Scraping method: Reddit API")
    print("• More reliable than web scraping")
    print("• Faster and more efficient")
    print("• No IP blocking issues")


def show_troubleshooting():
    """Show troubleshooting information"""
    print("\n🔧 TROUBLESHOOTING")
    print("=" * 30)
    print("If you encounter issues:")
    print()
    print("1. Invalid credentials error:")
    print("   • Double-check your CLIENT_ID and CLIENT_SECRET")
    print("   • Make sure you selected 'script' as app type")
    print()
    print("2. PRAW not found error:")
    print("   • Install PRAW: pip install praw")
    print()
    print("3. Rate limiting:")
    print("   • Reddit API has rate limits")
    print("   • The scraper automatically handles delays")
    print()
    print("4. Access denied:")
    print("   • Some subreddits may be private")
    print("   • Try with public subreddits first")
    print()
    print("5. Need help?")
    print("   • Check Reddit API documentation")
    print("   • Visit r/redditdev for help")


def main():
    """Main setup function"""
    print_header()
    
    try:
        # Check if config file exists
        if not Path("config.yaml").exists():
            print("❌ config.yaml not found!")
            print("Please run this script from the project root directory.")
            sys.exit(1)
        
        # Step 1: Open Reddit apps page
        open_reddit_apps_page()
        
        # Step 2: Get credentials
        client_id, client_secret = get_api_credentials()
        if not client_id or not client_secret:
            print("❌ Setup cancelled - credentials required")
            sys.exit(1)
        
        # Step 3: Optional authentication
        username, password = get_optional_credentials()
        
        # Step 4: Update config
        if not update_config_file(client_id, client_secret, username, password):
            print("❌ Setup failed - could not update config")
            sys.exit(1)
        
        # Step 5: Test connection
        if test_api_connection():
            show_next_steps()
        else:
            print("\n⚠️  Setup completed but connection test failed")
            print("You may need to install PRAW or check your credentials")
            show_troubleshooting()
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        show_troubleshooting()
        sys.exit(1)


if __name__ == "__main__":
    main()
