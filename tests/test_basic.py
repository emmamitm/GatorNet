import unittest
import pytest
import os
import sys
from pathlib import Path

# Check if module can be imported correctly
try:
    from AI.AI_model import QueryAnalyzer, ConversationState
    IMPORT_SUCCESS = True
except ImportError as e:
    IMPORT_SUCCESS = False
    IMPORT_ERROR = str(e)

class TestBasic(unittest.TestCase):
    def test_import(self):
        """Test that module imports are working"""
        self.assertTrue(IMPORT_SUCCESS, f"Import failed: {IMPORT_ERROR if not IMPORT_SUCCESS else ''}")
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module import failed")
    def test_query_analyzer_init(self):
        """Test that QueryAnalyzer can be initialized"""
        from AI.AI_model import QueryAnalyzer
        analyzer = QueryAnalyzer()
        self.assertIsNotNone(analyzer)
        
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module import failed")
    def test_simple_library_query(self):
        """Test a simple library hours query analysis"""
        from AI.AI_model import QueryAnalyzer
        analyzer = QueryAnalyzer()
        query = "What are the library hours today?"
        analysis = analyzer.analyze(query)
        self.assertEqual(analysis["intent"], "library_hours")
        self.assertTrue(analysis["is_hours_query"])
        
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module import failed")
    def test_conversation_state(self):
        """Test that ConversationState works properly"""
        from AI.AI_model import ConversationState
        state = ConversationState()
        state.add_message("User", "Hello")
        state.add_message("Assistant", "Hi there!")
        history = state.get_history()
        self.assertIn("User: Hello", history)
        self.assertIn("Assistant: Hi there!", history)

if __name__ == '__main__':
    unittest.main()
