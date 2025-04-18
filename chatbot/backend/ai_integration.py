import sys
import os
import threading
import time
from datetime import datetime
import traceback
import subprocess
import re

class AIWrapper:
    def __init__(self, model_path=None):
        print("AIWrapper initialization started")
        # We'll use subprocess to run the AI_model.py directly
        self.model_path = model_path
        self.ai_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AI")
        self.ai_script = os.path.join(self.ai_dir, "AI_model.py")
        
        # Verify the script exists
        if not os.path.exists(self.ai_script):
            print(f"AI script not found at: {self.ai_script}")
            raise FileNotFoundError(f"AI_model.py not found at {self.ai_script}")
        
        print(f"AIWrapper initialized with script: {self.ai_script}")
            
    def process_query(self, query):
        """Process a query by running the AI_model.py script directly"""
        print(f"Processing query via direct script: '{query}'")
        try:
            # Run the AI model script with the query as input
            result = subprocess.run(
                [sys.executable, self.ai_script, "--query", query],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(self.ai_script)
            )
            
            # Extract the response from the output
            output = result.stdout
            
            # Find the model's response in the output (everything after the query)
            try:
                # Look for the query line and take everything after it
                query_line = f"> {query}"
                if query_line in output:
                    response_start = output.index(query_line) + len(query_line)
                    response = output[response_start:].strip()
                    
                    # Remove any trailing prompt or other noise
                    if ">" in response:
                        response = response.split(">")[0].strip()
                    
                    # Simple but effective cleanup
                    response = self._clean_response(response)
                        
                    print(f"Response length: {len(response)} characters")
                    return response
                else:
                    # If query pattern not found, just apply cleanup to full output
                    response = self._clean_response(output)
                    return response
                    
            except Exception as e:
                print(f"Error parsing AI output: {e}")
                traceback.print_exc()
                
                # Last resort - apply cleanup to full output
                response = self._clean_response(output)
                return response
            
        except Exception as e:
            print(f"Error running AI script: {e}")
            traceback.print_exc()
            return f"I encountered an error processing your query: {str(e)}. Please try a different question."

    def _clean_response(self, text):
        """Clean AI response text by removing template/debug information and assistant tags."""
        
        # First, try to extract just the actual response if we can identify it clearly
        # Look for patterns that indicate the start of an actual response
        response_start_patterns = [
            "Hi there!",
            "I'm sorry,",
            "I apologize,",
            "Thank you for",
            "To answer your",
            "Here's",
            "The University"
        ]
        
        # Look for patterns that indicate the end of a response - text after these should be removed
        response_end_patterns = [
            "End User Question:",
            "User Question:",
            "assistant",
            "assistant:",
            "AI End User Question:",
            "You are the UF Assistant,",
            "Please provide a helpful response",
            "User:",
            "\n\n\n"  # Triple newline often separates response from template
        ]
        
        # First pass - try to extract clean response between common markers
        if "Hi there!" in text and any(pattern in text for pattern in response_end_patterns):
            # Find the start of relevant content
            start_pos = text.find("Hi there!")
            
            # Find the earliest end marker
            end_pos = len(text)
            for pattern in response_end_patterns:
                pos = text.find(pattern, start_pos)
                if pos != -1 and pos < end_pos:
                    end_pos = pos
            
            # Extract just the response portion
            if start_pos < end_pos:
                text = text[start_pos:end_pos].strip()
        
        # Try another approach - find a clear start pattern if we haven't already
        if not any(pattern in text[:50] for pattern in response_start_patterns):
            for pattern in response_start_patterns:
                if pattern in text:
                    text = text[text.find(pattern):].strip()
                    break
        
        # Remove any end markers and everything after them
        for pattern in response_end_patterns:
            if pattern in text:
                text = text[:text.find(pattern)].strip()
        
        # Handle specific variations that might appear
        text = re.sub(r'assistant$', '', text).strip()
        text = re.sub(r'Sincerely, The UF Assistant.*$', 'Sincerely, The UF Assistant', text, flags=re.DOTALL).strip()
        
        # Remove any lines containing "UF Assistant AI" which often marks template boundaries
        lines = text.split('\n')
        cleaned_lines = [line for line in lines if "UF Assistant AI" not in line]
        text = '\n'.join(cleaned_lines)
        
        # List of markers that indicate the start of template/debug information
        end_markers = [
            "```\nResponse Type:",
            "Response Type:",
            "```python not modify",
            "def respond_to_user", 
            "import random",
            "response_map =",
            "a dictionary to map",
            "python not modify",
            "```\n```",  # Empty code block often indicates template boundary
            "**Response**",
            "**Output**",
            "await response",
            "<assistant>",
            "</assistant>"
        ]
        
        # Find the position of the earliest marker
        earliest_pos = len(text)
        for marker in end_markers:
            pos = text.find(marker)
            if pos != -1 and pos < earliest_pos:
                earliest_pos = pos
        
        # If any marker was found, truncate the text
        if earliest_pos < len(text):
            text = text[:earliest_pos].strip()
        
        # Handle special case of code blocks without language specifier that contain template info
        unlabeled_code_blocks = re.findall(r'```\n[\s\S]*?```', text)
        for block in unlabeled_code_blocks:
            if any(marker in block for marker in ["Response Type:", "Tone:", "Intent:", "import random", "def respond_to_user"]):
                text = text.replace(block, "")
        
        # Clean up any incomplete markdown elements
        if text.count("```") % 2 != 0:  # Odd number of code block markers
            # Find the last complete code block
            last_complete = text.rfind("```", 0, text.rfind("```"))
            if last_complete != -1:
                # Find the end of this code block
                end_of_block = text.find("```", last_complete + 3)
                if end_of_block != -1:
                    # Keep everything up to and including this code block
                    text = text[:end_of_block + 3].strip()
                else:
                    # If we can't find the end, just truncate at the last starting marker
                    text = text[:last_complete].strip()
        
        # Remove any other common template artifacts
        artifacts_to_remove = [
            r'You are the UF Assistant.*?$',
            r'User Question:.*?$',
            r'User asked:.*?$',
            r'Please provide a helpful.*?$'
        ]
        
        for pattern in artifacts_to_remove:
            text = re.sub(pattern, '', text, flags=re.MULTILINE | re.DOTALL).strip()
        
        # Replace any occurrence of "assistant: " pattern in the middle of text
        assistant_pattern = re.compile(r'assistant:?\s?', re.IGNORECASE)
        if assistant_pattern.search(text):
            parts = assistant_pattern.split(text, 1)
            if parts[0].strip():  # If there's content before the first "assistant:" tag
                text = parts[0].strip()
            else:  # If "assistant:" is at the beginning, use the second part but check for further occurrences
                remaining_text = parts[1]
                # Check for more "assistant:" patterns in the remaining text
                more_parts = assistant_pattern.split(remaining_text)
                text = more_parts[0].strip()
        
        # Handle the "[insert link]" pattern and replace with UF main page link
        text = text.replace("[insert link]", "[UF Website](https://www.ufl.edu)")
        
        # Final pass to remove any leftover template/assistant references
        text = re.sub(r'\bassistant\b', '', text, flags=re.IGNORECASE).strip()
        
        return text.strip()

class AIManager:
    def __init__(self):
        # Initialize the UF Assistant immediately
        self._assistant = None
        self._assistant_lock = threading.Lock()
        self._initialization_error = None
        
        # Default model path - update this to your actual model path
        self.model_path = "./AI/models/Meta-Llama-3-8B-Instruct-Q8_0.gguf"
        
        # Initialize the assistant right away
        print("Initializing Enhanced UF Assistant...")
        self._initialize_assistant()
    
    def _initialize_assistant(self):
        """Initialize the assistant immediately"""
        try:
            print("Starting AI initialization...")
            with self._assistant_lock:
                # Use AIWrapper with subprocess approach
                self._assistant = AIWrapper(model_path=self.model_path)
                print("AI initialization complete!")
                
        except Exception as e:
            print(f"Error initializing AI: {e}")
            traceback.print_exc()
            self._initialization_error = str(e)
    
    def _get_fallback_response(self, message):
        """Simple fallback responses when AI is not available"""
        message = message.lower()
        
        if "library" in message and "hour" in message:
            return "Most UF libraries are open from 7am to 2am on weekdays, with reduced hours on weekends. You can check the UF Libraries website for specific library hours."
            
        elif "event" in message:
            return "For information about UF events, I recommend checking the official UF calendar at calendar.ufl.edu."
            
        else:
            return "I apologize, but my AI capabilities are currently unavailable. Please try again later."
    
    def process_message(self, message, conversation_id, user_id):
        """Process a user message and store both message and response in the database"""
        # Delayed import to prevent circular imports
        from database_tables import db, Message
        
        print(f"AI processing message: '{message}' for conversation {conversation_id}, user {user_id}")
        
        # Generate AI response
        ai_response = ""
        
        # Use full AI if available
        if self._assistant is not None:
            try:
                print("Using AI assistant to generate response")
                ai_response = self._assistant.process_query(message)
                print(f"AI Response: {ai_response[:100]}...")  # Log first 100 chars of response
            except Exception as e:
                print(f"Error generating AI response: {e}")
                traceback.print_exc()  # Add full traceback for better debugging
                ai_response = self._get_fallback_response(message)
        else:
            print("AI not initialized, using fallback response")
            ai_response = self._get_fallback_response(message)
        
        # Ensure we have a response
        if not ai_response:
            ai_response = "I apologize, but I encountered an issue processing your request. Please try again."
        
        # Store user message and AI response in database
        try:
            # Add user message
            user_message = Message(
                conversation_id=conversation_id,
                user_id=user_id,
                text=message,
                sent_at=datetime.now()
            )
            db.session.add(user_message)
            
            # Add AI response with user_id=0 (AI user)
            ai_message = Message(
                conversation_id=conversation_id,
                user_id=0,  # Special AI user ID
                text=ai_response,
                sent_at=datetime.now()
            )
            db.session.add(ai_message)
            db.session.commit()
            print(f"Successfully saved messages to database")
        except Exception as e:
            db.session.rollback()
            print(f"Error saving messages: {str(e)}")
            traceback.print_exc()
        
        return ai_response

# Create a singleton instance
ai_manager = AIManager()