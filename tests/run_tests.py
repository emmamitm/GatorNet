#!/usr/bin/env python3
import unittest
import sys
import os
import pytest

def run_tests():
    """Run all tests using pytest"""
    # Configure test environment
    os.environ["PYTHONPATH"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Run the tests
    print("\n================ Running Basic Tests ================")
    basic_result = pytest.main(["-v", "tests/test_basic.py"])
    
    print("\n================ Running Unit Tests ================")
    unit_result = pytest.main(["-v", "tests/test_unit.py"])
    
    print("\n================ Running Integration Tests ================")
    integration_result = pytest.main(["-v", "tests/test_integration_fixed.py"])
    
    print("\n================ Running System Tests ================")
    system_result = pytest.main(["-v", "tests/test_system.py"])
    
    # Determine overall result
    success = (basic_result == 0 and unit_result == 0 and 
               integration_result == 0 and system_result == 0)
    
    if success:
        print("\n✅ All tests passed successfully!")
    else:
        print("\n❌ Some tests failed. Check the logs above for details.")
    
    return success

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
