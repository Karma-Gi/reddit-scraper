#!/usr/bin/env python3
"""
Quick test to verify the database connection fixes
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.data_processor import DataProcessor
from src.labeling_system import LabelingSystem
from src.utils import load_config, log_message


def test_data_processor():
    """Test DataProcessor with new database manager"""
    print("🧪 Testing DataProcessor...")
    
    try:
        processor = DataProcessor()
        
        # Test getting stats
        stats = processor.get_processing_stats()
        print(f"✅ DataProcessor stats: {stats}")
        
        # Test processing a few posts (if any unprocessed exist)
        if stats['total_posts'] > stats['processed_posts']:
            print("📝 Processing remaining posts...")
            processed = processor.process_all_posts()
            print(f"✅ Processed {processed} posts")
        else:
            print("✅ All posts already processed")
        
        return True
        
    except Exception as e:
        print(f"❌ DataProcessor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_labeling_system():
    """Test LabelingSystem with new database manager"""
    print("\n🏷️ Testing LabelingSystem...")
    
    try:
        labeler = LabelingSystem()
        
        # Test getting stats
        stats = labeler.get_labeling_stats()
        print(f"✅ LabelingSystem stats: {stats}")
        
        # Test labeling posts (if any unlabeled exist)
        if stats['total_labeled'] < 10:  # If less than 10 posts labeled
            print("🏷️ Labeling posts...")
            labeled = labeler.label_all_posts()
            print(f"✅ Labeled {labeled} posts")
        else:
            print("✅ Posts already labeled")
        
        return True
        
    except Exception as e:
        print(f"❌ LabelingSystem test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print("🔧 TESTING DATABASE CONNECTION FIXES")
    print("=" * 50)
    
    # Test DataProcessor
    processor_ok = test_data_processor()
    
    # Test LabelingSystem
    labeler_ok = test_labeling_system()
    
    print("\n" + "=" * 50)
    if processor_ok and labeler_ok:
        print("✅ ALL TESTS PASSED!")
        print("🎉 Database connection fixes are working correctly")
        print("\nYou can now run:")
        print("  python main.py --full")
        print("  python main.py --process")
        print("  python main.py --label")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the error messages above")


if __name__ == "__main__":
    main()
