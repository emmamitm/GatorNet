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
                    
                    # ADVANCED CLEANUP
                    # Preserve markdown content but clean up after it
                    response = self._clean_preserving_markdown(response)
                        
                    print(f"Response length: {len(response)} characters")
                    return response
                else:
                    # If query pattern not found, try to extract meaningful response
                    response = self._extract_meaningful_response(output)
                    return response
                    
            except Exception as e:
                print(f"Error parsing AI output: {e}")
                
                # Last resort cleanup - try to extract meaningful response
                response = self._extract_meaningful_response(output)
                return response
            
        except Exception as e:
            print(f"Error running AI script: {e}")
            traceback.print_exc()
            return f"I encountered an error processing your query: {str(e)}. Please try a different question."

    def _clean_preserving_markdown(self, text):
        """Clean text while preserving markdown formatting"""
        # Identify the end of markdown content
        # Looking for common markers that appear after the main content
        markdown_end_markers = [
            "assistant",
            "Context Information",
            "User Question:",
            "(Note:",
            "# UF",
            "**Response**",
            "**Output**"
        ]
        
        # Find the position of the earliest marker
        earliest_pos = len(text)
        for marker in markdown_end_markers:
            pos = text.find(marker)
            if pos != -1 and pos < earliest_pos:
                # Don't cut at bold/italic markers that might be part of markdown
                if marker in ["**Response**", "**Output**"]:
                    # Check if this is actually part of markdown formatting
                    # or if it appears to be a template header
                    pattern = r'\*\*' + marker.strip('*') + r'\*\*\s*[\n:]'
                    if re.search(pattern, text):
                        earliest_pos = pos
                else:
                    earliest_pos = pos
        
        # If any marker was found, truncate the text
        if earliest_pos < len(text):
            text = text[:earliest_pos].strip()
        
        # Clean up specific patterns that might be mixed with markdown
        # Only clean patterns that appear to be template instructions
        
        # Remove hashtags if they appear to be tags, not markdown headers
        # Markdown headers have # at start of line, tags usually have space before #
        text = re.sub(r'(?<!\n)\s+#\s*[A-Za-z0-9]+', '', text)
        
        # Remove template sections with "Hi there! I'm the UF Assistant" that repeat
        if text.count("Hi there! I'm the UF Assistant") > 1:
            parts = text.split("Hi there! I'm the UF Assistant")
            text = "Hi there! I'm the UF Assistant" + parts[1]
            
        return text.strip()
        
    def _extract_meaningful_response(self, output):
        """Extract meaningful response from output when regular patterns fail"""
        # Split by lines and try different extraction methods
        lines = output.split('\n')
        
        # Filter out diagnostic/debug lines
        filtered_lines = [line for line in lines if not line.startswith("✓") and 
                        "Found scrapedData" not in line and
                        "Contains" not in line and
                        "setting HOME_DIR" not in line]
        
        # Try to find a response starting with common greeting patterns
        start_idx = -1
        for i, line in enumerate(filtered_lines):
            if any(greeting in line for greeting in ["Hi", "Hello", "Welcome", "Greetings", "I'm", "Thank"]):
                start_idx = i
                break
        
        if start_idx >= 0:
            # Get all lines from starting point
            response_lines = filtered_lines[start_idx:]
            response = "\n".join(response_lines)
        else:
            # If no greeting found, just use all filtered lines
            response = "\n".join(filtered_lines)
        
        # Apply the markdown-preserving cleanup
        response = self._clean_preserving_markdown(response)
        
        return response.strip()

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