#!/usr/bin/env python3
"""
Test runner for the Reddit Study Abroad Data Scraper
"""

import unittest
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

def run_all_tests():
    """Run all unit tests"""
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()

def run_specific_test(test_module):
    """Run a specific test module"""
    try:
        # Import the test module
        module = __import__(f'tests.{test_module}', fromlist=[test_module])
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"Error importing test module {test_module}: {e}")
        return False

def main():
    """Main test runner function"""
    print("Reddit Study Abroad Data Scraper - Test Runner")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        # Run specific test
        test_module = sys.argv[1]
        if not test_module.startswith('test_'):
            test_module = f'test_{test_module}'
        
        print(f"Running specific test: {test_module}")
        success = run_specific_test(test_module)
    else:
        # Run all tests
        print("Running all tests...")
        success = run_all_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
