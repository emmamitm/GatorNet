import unittest
import pytest
from unittest.mock import MagicMock, patch
import os
import sys

class TestUFAssistantIntegration(unittest.TestCase):
    @patch('AI.AI_model.SentenceTransformer')
    @patch('AI.AI_model.load_campus_buildings_data')
    @patch('AI.AI_model.load_libraries_data')
    @patch('AI.AI_model.load_hallinfo_data')
    @patch('AI.AI_model.load_clubs_data')
    def setUp(self, mock_clubs, mock_dorms, mock_libraries, mock_buildings, mock_transformer):
        from AI.AI_model import EnhancedUFAssistant
        
        # Configure mocks to return realistic test data
        mock_transformer.return_value = MagicMock()
        
        mock_buildings.return_value = [
            {
                "Building Name": "Reitz Union",
                "Building Number": "J401",
                "Abbreviation": "REITZ",
                "Address": "686 Museum Road, Gainesville, FL 32611",
                "Description": "The J. Wayne Reitz Union is the student union of the University of Florida."
            },
            {
                "Building Name": "Library West",
                "Building Number": "LBW",
                "Abbreviation": "LW",
                "Address": "1545 W University Ave, Gainesville, FL 32611",
                "Description": "Library West is the main library at UF."
            }
        ]
        
        mock_libraries.return_value = [
            {
                "Library Name": "Library West",
                "Location": "1545 W University Ave",
                "Hours": {
                    "Monday": "8am - 10pm",
                    "Tuesday": "8am - 10pm",
                    "Wednesday": "8am - 10pm",
                    "Thursday": "8am - 10pm",
                    "Friday": "8am - 6pm",
                    "Saturday": "10am - 6pm",
                    "Sunday": "12pm - 10pm"
                },
                "Special Notes": "Extended hours during finals"
            },
            {
                "Library Name": "Marston Science Library",
                "Location": "444 Newell Dr",
                "Hours": {
                    "Monday": "8am - 9pm",
                    "Tuesday": "8am - 9pm",
                    "Wednesday": "8am - 9pm",
                    "Thursday": "8am - 9pm",
                    "Friday": "8am - 6pm",
                    "Saturday": "10am - 6pm",
                    "Sunday": "12pm - 9pm"
                },
                "Special Notes": "Houses STEM collections"
            }
        ]
        
        mock_dorms.return_value = [
            {
                "Building Name": "Hume Hall",
                "Hall Type": "honors",
                "Description": "Hume Hall is a residence hall for honors students.",
                "Location": "Museum Road",
                "Features": ["Study lounges", "Air conditioning", "Suite-style rooms"]
            },
            {
                "Building Name": "Broward Hall",
                "Hall Type": "traditional",
                "Description": "Broward Hall is a traditional residence hall for first-year students.",
                "Location": "Broward Drive",
                "Features": ["Community bathrooms", "Air conditioning", "Study areas"]
            }
        ]
        
        mock_clubs.return_value = [
            {
                "Club ID": "1001",
                "Organization Name": "Gator Robotics",
                "Description": "Gator Robotics is a student organization dedicated to robotics competitions and projects."
            },
            {
                "Club ID": "1002",
                "Organization Name": "Chess Club",
                "Description": "The UF Chess Club welcomes players of all skill levels."
            }
        ]
        
        # Initialize the assistant with additional mocking
        with patch('AI.AI_model.LlamaModelConfig.initialize_model') as mock_llm_init:
            mock_llm_init.return_value = MagicMock(return_value={"choices": [{"text": "Mock LLM response"}]})
            # Initialize with minimal config
            self.assistant = EnhancedUFAssistant()
        
        # Replace the LLM with a mock
        self.assistant.llm = MagicMock()
        self.assistant.llm.return_value = {"choices": [{"text": "This is a response from the mock LLM."}]}
        
    def test_conversation_flow(self):
        """Test a simple conversation flow with the assistant"""
        # Test a simple query - should work even without complex setup
        response = self.assistant.process_query("Hello")
        self.assertIsNotNone(response)
        self.assertTrue(isinstance(response, str))
        self.assertTrue(len(response) > 0)
        
        # The LLM mock should have been called
        self.assistant.llm.assert_called()

if __name__ == '__main__':
    unittest.main()
