#!/usr/bin/env python3
"""
Fixed test runner for NREL Weather Data Connector.

Runs all unit tests with proper cache isolation.
"""

import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_tests():
    """Run all unit tests with isolated cache directories."""
    
    # Create a completely isolated temporary directory for all tests
    temp_test_dir = tempfile.mkdtemp(prefix='nrel_test_')
    
    try:
        # Import and patch the config to use our isolated directory
        from nrel.config import Config
        original_cache_dir = Config().cache_dir
        Config().cache_dir = Path(temp_test_dir)
        
        print(f"Using isolated test cache directory: {temp_test_dir}")
        
        # Discover and run all tests
        loader = unittest.TestLoader()
        test_dir = Path(__file__).parent / 'tests'
        suite = loader.discover(str(test_dir), pattern='test_*.py')
        
        # Run tests with detailed output
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        # Restore original cache directory
        Config().cache_dir = original_cache_dir
        
        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
        
        if result.failures:
            print(f"\nFAILURES ({len(result.failures)}):")
            for test, traceback in result.failures:
                print(f"  - {test}")
                if len(result.failures) <= 3:  # Show details for few failures
                    print(f"    {traceback.split(chr(10))[-2]}")  # Last line of traceback
        
        if result.errors:
            print(f"\nERRORS ({len(result.errors)}):")
            for test, traceback in result.errors:
                print(f"  - {test}")
                if len(result.errors) <= 3:  # Show details for few errors
                    print(f"    {traceback.split(chr(10))[-2]}")  # Last line of traceback
        
        success = len(result.failures) == 0 and len(result.errors) == 0
        
        if success:
            print(f"\n✓ All tests passed!")
            return True
        else:
            print(f"\n✗ Some tests failed. See details above.")
            return False
            
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_test_dir)
        except Exception as e:
            print(f"Warning: Could not clean up temp directory {temp_test_dir}: {e}")

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)