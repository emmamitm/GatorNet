import unittest
import pytest
from unittest.mock import MagicMock, patch
import os
import sys
import tempfile
import json

class TestUFAssistantSystem(unittest.TestCase):
    """System tests for the GatorNet AI assistant that verify end-to-end functionality."""
    
    @classmethod
    @patch('AI.AI_model.SentenceTransformer')
    def setUpClass(cls, mock_transformer):
        """Set up a real EnhancedUFAssistant instance with mocked dependencies for system testing"""
        from AI.AI_model import EnhancedUFAssistant
        
        # Mock the transformer
        mock_transformer.return_value = MagicMock()
        mock_transformer.return_value.encode = MagicMock(return_value=[0.1] * 384)  # Fake embeddings
        
        # Create a temp directory for test data
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.data_dir = cls.temp_dir.name
        
        # Create test directories
        os.makedirs(os.path.join(cls.data_dir, "scrapedData", "campusBuildings"), exist_ok=True)
        os.makedirs(os.path.join(cls.data_dir, "scrapedData", "campusClubs"), exist_ok=True)
        os.makedirs(os.path.join(cls.data_dir, "scrapedData", "libraries"), exist_ok=True)
        os.makedirs(os.path.join(cls.data_dir, "scrapedData", "housing"), exist_ok=True)
        os.makedirs(os.path.join(cls.data_dir, "scrapedData", "classes"), exist_ok=True)
        os.makedirs(os.path.join(cls.data_dir, "scrapedData", "campusEvents"), exist_ok=True)
        
        # Create test CSV files
        buildings_csv = "number,name,abbreviation,address,description\n" \
                       "101,Library West,LBW,1545 W University Ave,Main library at UF\n" \
                       "102,Marston Science Library,MSL,444 Newell Dr,Science library\n" \
                       "103,Reitz Union,REITZ,686 Museum Rd,Student union"
                       
        libraries_csv = "Library Name,Location,Capacity,Hours,Special Notes,URL,Phone,Email\n" \
                       "Library West,1545 W University Ave,500,8am-10pm,Main library,http://lib.ufl.edu,123-456-7890,test@ufl.edu\n" \
                       "Marston Science Library,444 Newell Dr,400,8am-9pm,Science library,http://lib.ufl.edu,123-456-7891,marston@ufl.edu"
                       
        dorms_csv = "name,hall_type,description,location,phone,features_str,room_types_str,nearby_locations_str,url,image_url,rental_rate_url\n" \
                   "Broward Hall,traditional,Freshman dorm,Broward Dr,123-456-7890,AC;WiFi,Single;Double,Dining;Gym,url,img,rates\n" \
                   "Hume Hall,honors,Honors dorm,Museum Rd,123-456-7891,Study rooms;AC,Single;Double,Library;Gym,url,img,rates"
                   
        clubs_csv = "ID,Organization Name,Description\n" \
                   "1001,Gator Programming,Coding club at UF\n" \
                   "1002,Chess Club,Chess club at UF"
                   
        majors_csv = "Department,Description\n" \
                    "Computer Science,Study of computing and programming\n" \
                    "Psychology,Study of human behavior"
                    
        programs_csv = "Department,Name,URL,Type\n" \
                      "Computer Science,Computer Science,/cs,Major\n" \
                      "Psychology,Psychology,/psych,Major"
                      
        courses_csv = "department,code,title,credits,description,prerequisites,grading_scheme\n" \
                     "Computer Science,COP3502,Programming Fundamentals 1,3,Intro to programming,MAC1140,Letter\n" \
                     "Psychology,PSY2012,General Psychology,3,Intro to psychology,None,Letter"
                     
        events_csv = "name,date,time,location,link,description\n" \
                    "Gator Nights,2025-04-25,8:00 PM,Reitz Union,link,Weekly event\n" \
                    "Study Session,2025-04-30,6:00 PM,Library West,link,Finals prep"
        
        # Write test files
        with open(os.path.join(cls.data_dir, "scrapedData", "campusBuildings", "uf_buildings.csv"), "w") as f:
            f.write(buildings_csv)
            
        with open(os.path.join(cls.data_dir, "scrapedData", "libraries", "uf_libraries.csv"), "w") as f:
            f.write(libraries_csv)
            
        with open(os.path.join(cls.data_dir, "scrapedData", "housing", "hallInfo.csv"), "w") as f:
            f.write(dorms_csv)
            
        with open(os.path.join(cls.data_dir, "scrapedData", "campusClubs", "uf_organizations.csv"), "w") as f:
            f.write(clubs_csv)
            
        with open(os.path.join(cls.data_dir, "scrapedData", "classes", "majors.csv"), "w") as f:
            f.write(majors_csv)
            
        with open(os.path.join(cls.data_dir, "scrapedData", "classes", "programs.csv"), "w") as f:
            f.write(programs_csv)
            
        with open(os.path.join(cls.data_dir, "scrapedData", "classes", "courses.csv"), "w") as f:
            f.write(courses_csv)
            
        with open(os.path.join(cls.data_dir, "scrapedData", "campusEvents", "uf_events_all.csv"), "w") as f:
            f.write(events_csv)
        
        # Store original env variable
        cls.original_data_dir = os.environ.get("AI_DATA_DIR")
        
        # Set up environment for testing
        os.environ["AI_DATA_DIR"] = cls.data_dir
        
        # Initialize the assistant with LLM mocking
        with patch('AI.AI_model.LlamaModelConfig.initialize_model') as mock_init:
            mock_init.return_value = MagicMock(return_value={"choices": [{"text": "Mock LLM response"}]})
            cls.assistant = EnhancedUFAssistant()
        
        # Replace the LLM with a mock that returns predictable responses
        cls.assistant.llm = MagicMock()
        cls.assistant.llm.return_value = {"choices": [{"text": "This is a mock response about UF."}]}
    
    @classmethod
    def tearDownClass(cls):
        """Clean up temporary files and restore environment"""
        # Restore original env variable
        if cls.original_data_dir:
            os.environ["AI_DATA_DIR"] = cls.original_data_dir
        else:
            del os.environ["AI_DATA_DIR"]
            
        cls.temp_dir.cleanup()
    
    def test_greeting_response(self):
        """Test that the assistant responds appropriately to greetings"""
        greetings = ["Hello", "Hi", "Hey there", "Good morning"]
        
        for greeting in greetings:
            response = self.assistant.process_query(greeting)
            self.assertIsNotNone(response)
            self.assertTrue(isinstance(response, str))
            self.assertTrue(len(response) > 0)
            
    def test_library_information_query(self):
        """Test that the assistant handles library information queries"""
        query = "Tell me about Library West"
        response = self.assistant.process_query(query)
        
        self.assertIsNotNone(response)
        self.assertTrue("Library West" in response)
        
    def test_building_location_query(self):
        """Test that the assistant handles building location queries"""
        query = "Where is the Reitz Union?"
        response = self.assistant.process_query(query)
        
        self.assertIsNotNone(response)
        self.assertTrue("Reitz Union" in response)
        
    def test_conversation_context(self):
        """Test that the assistant maintains conversation context across turns"""
        # Reset conversation state
        self.assistant.reset_conversation()
        
        # First query about Library West
        query1 = "What are the hours for Library West?"
        response1 = self.assistant.process_query(query1)
        
        # Follow-up query that relies on context
        query2 = "Where is it located?"
        response2 = self.assistant.process_query(query2)
        
        # Should mention Library West in the response to the follow-up
        self.assertTrue("Library West" in response2 or "1545 W University Ave" in response2)
        
    def test_error_handling(self):
        """Test that the assistant gracefully handles errors"""
        # Create a query that might cause errors
        query = "Tell me about a non-existent building"
        
        # Shouldn't raise exceptions
        try:
            response = self.assistant.process_query(query)
            self.assertIsNotNone(response)
            self.assertTrue(isinstance(response, str))
            self.assertTrue(len(response) > 0)
        except Exception as e:
            self.fail(f"process_query raised an exception: {e}")
            
    def test_multiple_intents(self):
        """Test that the assistant can handle different query intents"""
        intents = {
            "library_hours": "When does Library West close?",
            "building_location": "Where is the Reitz Union?",
            "dorm_info": "Tell me about Broward Hall",
            "major_info": "What's the Computer Science major like?"
        }
        
        for intent, query in intents.items():
            response = self.assistant.process_query(query)
            self.assertIsNotNone(response)
            self.assertTrue(len(response) > 0)

if __name__ == '__main__':
    unittest.main()
