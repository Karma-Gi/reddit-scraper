#!/usr/bin/env python3
"""
Test language detection accuracy on Reddit study abroad content
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils import detect_language
from src.database_manager import create_database_manager
from src.utils import load_config


def test_language_detection_samples():
    """Test language detection on sample texts"""
    print("🧪 TESTING LANGUAGE DETECTION")
    print("=" * 40)
    
    # Sample texts that should be detected as English
    test_texts = [
        "I'm applying to MIT for Computer Science PhD program. Any advice?",
        "Stanford is very competitive for Engineering. I got rejected.",
        "What are my chances for Harvard with a 3.8 GPA?",
        "Looking for recommendations for good CS programs",
        "Anyone know about financial aid at UC Berkeley?",
        "How difficult is it to get into grad school?",
        "SAT scores required for top universities",
        "International student applying to US colleges",
        "Research experience needed for PhD applications",
        "Best universities for machine learning research"
    ]
    
    print("Testing sample texts:")
    correct_detections = 0
    
    for i, text in enumerate(test_texts, 1):
        detected = detect_language(text)
        is_correct = detected == 'en'
        status = "✅" if is_correct else "❌"
        
        print(f"{status} {i:2d}. '{text[:50]}...' → {detected}")
        
        if is_correct:
            correct_detections += 1
    
    accuracy = correct_detections / len(test_texts) * 100
    print(f"\n📊 Accuracy: {correct_detections}/{len(test_texts)} ({accuracy:.1f}%)")
    
    return accuracy


def test_database_content():
    """Test language detection on actual database content"""
    print("\n🗄️ TESTING DATABASE CONTENT")
    print("=" * 40)
    
    try:
        config = load_config()
        db_manager = create_database_manager(config)
        db_manager.connect()
        
        # Get sample posts
        query = """
            SELECT id, question_title, answer_content_cleaned
            FROM posts 
            WHERE answer_content_cleaned IS NOT NULL
            ORDER BY id 
            LIMIT 20
        """
        
        posts = db_manager.execute_query(query)
        
        if not posts:
            print("❌ No posts found in database")
            return
        
        print(f"Testing {len(posts)} posts from database:")
        
        english_count = 0
        non_english_count = 0
        
        for post in posts:
            if db_manager.db_type == 'mysql':
                post_id, title, content = post['id'], post['question_title'], post['answer_content_cleaned']
            else:
                post_id, title, content = post[0], post[1], post[2]
            
            if content:
                detected = detect_language(content)
                is_english = detected == 'en'
                status = "🇺🇸" if is_english else f"🌍({detected})"
                
                display_text = title[:40] if title else content[:40]
                print(f"{status} Post {post_id}: {display_text}...")
                
                if is_english:
                    english_count += 1
                else:
                    non_english_count += 1
        
        total = english_count + non_english_count
        if total > 0:
            english_pct = english_count / total * 100
            print(f"\n📊 Results:")
            print(f"  English: {english_count}/{total} ({english_pct:.1f}%)")
            print(f"  Non-English: {non_english_count}/{total} ({100-english_pct:.1f}%)")
            
            if non_english_count > total * 0.5:
                print("⚠️  WARNING: High non-English detection rate!")
                print("   This suggests the language detection might be inaccurate.")
                print("   Consider keeping 'enable_language_filter: false'")
        
        db_manager.close()
        
    except Exception as e:
        print(f"❌ Error testing database content: {e}")


def show_language_config():
    """Show current language detection configuration"""
    print("\n⚙️ CURRENT CONFIGURATION")
    print("=" * 30)
    
    try:
        config = load_config()
        processing_config = config.get('processing', {})
        
        enable_filter = processing_config.get('enable_language_filter', False)
        target_lang = processing_config.get('target_language', 'en')
        
        print(f"Language filter enabled: {enable_filter}")
        print(f"Target language: {target_lang}")
        
        if enable_filter:
            print("⚠️  Language filter is ENABLED")
            print("   Posts detected as non-English will be removed")
        else:
            print("✅ Language filter is DISABLED")
            print("   No posts will be removed based on language")
        
        return enable_filter
        
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return False


def main():
    """Main test function"""
    print("🌍 LANGUAGE DETECTION TESTING TOOL")
    print("=" * 50)
    
    # Test sample texts
    sample_accuracy = test_language_detection_samples()
    
    # Test database content
    test_database_content()
    
    # Show configuration
    filter_enabled = show_language_config()
    
    print("\n" + "=" * 50)
    print("📋 RECOMMENDATIONS:")
    
    if sample_accuracy < 80:
        print("❌ Language detection accuracy is low (<80%)")
        print("   Recommendation: Keep language filter DISABLED")
    else:
        print("✅ Language detection accuracy is acceptable (≥80%)")
        print("   You can enable language filter if needed")
    
    if filter_enabled:
        print("\n⚠️  CURRENT STATUS: Language filter is ENABLED")
        print("   If you're losing too many posts, disable it in config.yaml:")
        print("   processing:")
        print("     enable_language_filter: false")
    else:
        print("\n✅ CURRENT STATUS: Language filter is DISABLED")
        print("   This is the recommended setting for Reddit study abroad content")
    
    print("\n🔧 To change settings, edit config.yaml:")
    print("   processing:")
    print("     enable_language_filter: true/false")
    print("     target_language: 'en'")


if __name__ == "__main__":
    main()
