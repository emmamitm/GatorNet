import sys
import os
import threading
import time
from datetime import datetime
import traceback
import subprocess
import logging
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ai_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ai_integration")

class AIWrapper:
    """Wrapper for the AI model subprocess execution"""
    
    def __init__(self, model_path=None):
        logger.info("AIWrapper initialization started")
        # We'll use subprocess to run the AI_model.py directly
        self.model_path = model_path
        self.ai_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AI")
        self.ai_script = os.path.join(self.ai_dir, "AI_model.py")
        
        # Verify the script exists
        if not os.path.exists(self.ai_script):
            logger.error(f"AI script not found at: {self.ai_script}")
            raise FileNotFoundError(f"AI_model.py not found at {self.ai_script}")
        
        # Track active requests to prevent duplicates
        self._active_requests = set()
        
        logger.info(f"AIWrapper initialized with script: {self.ai_script}")
    
    def process_query(self, query, request_id=None):
        """Process a query by running the AI_model.py script directly with deduplication"""
        # Generate a request ID if none is provided
        if not request_id:
            request_id = str(uuid.uuid4())
            
        # Check if we already have this exact query in process
        query_key = f"{query}_{request_id}"
        if query_key in self._active_requests:
            logger.warning(f"Duplicate query detected: '{query}' with ID {request_id}")
            return "Your request is still being processed. Please wait a moment."
        
        logger.info(f"Processing query via direct script: '{query}' with ID {request_id}")
        
        try:
            # Mark this request as active
            self._active_requests.add(query_key)
            
            # Run the AI model script with the query as input
            result = subprocess.run(
                [sys.executable, self.ai_script, "--query", query],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(self.ai_script),
                timeout=60  # Add timeout to prevent hanging
            )
            
            # Extract the response from the output
            output = result.stdout
            
            # Simplified response extraction
            response = self._extract_response(output, query)
            
            # Log response length for debugging
            logger.info(f"Response generated: {len(response)} characters for request ID {request_id}")
            
            return response
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout occurred while processing query: '{query}'")
            return "I'm sorry, but it's taking me longer than expected to process your request. Please try a simpler question."
            
        except Exception as e:
            logger.error(f"Error running AI script: {e}")
            traceback.print_exc()
            return f"I encountered an error processing your request. Please try again or ask a different question."
            
        finally:
            # Remove from active requests when done
            self._active_requests.discard(query_key)
    
    def _extract_response(self, output, query):
        """Extract the model's response from subprocess output with improved robustness"""
        try:
            # If output is empty or None
            if not output:
                return "Sorry, I couldn't generate a response. Please try again."
            
            # Look for patterns in the output to extract the relevant response
            if "assistant:" in output.lower():
                # Split by assistant tag and take the part after it
                parts = output.lower().split("assistant:")
                if len(parts) > 1:
                    # Take the first part after "assistant:"
                    return parts[1].strip()
            
            # Check for query in output
            query_pattern = f"> {query}"
            if query_pattern in output:
                # Take everything after the query
                response_start = output.index(query_pattern) + len(query_pattern)
                response = output[response_start:].strip()
                
                # Remove any trailing prompt
                if ">" in response:
                    response = response.split(">")[0].strip()
                
                return response
            
            # Default to returning the cleaned output if no patterns match
            return output.strip()
            
        except Exception as e:
            logger.error(f"Error parsing AI output: {e}")
            return output.strip()  # Return original output if parsing fails

class AIManager:
    """Manager class for handling AI model initialization and request processing"""
    
    def __init__(self):
        # Initialize the UF Assistant with a lazy loading mechanism
        self._assistant = None
        self._assistant_lock = threading.Lock()
        self._initialization_thread = None
        self._initialization_error = None
        self._is_initializing = False
        
        # Request tracking for deduplication
        self._request_history = {}
        self._request_lock = threading.Lock()
        self._request_cooldown = 1.5  # seconds
        
        # Default model path - update this to your actual model path
        self.model_path = "./AI/models/Meta-Llama-3-8B-Instruct-Q8_0.gguf"
        
        logger.info("AIManager initialized")
    
    @property
    def assistant(self):
        """Lazy-load the assistant when first needed with improved thread safety"""
        with self._assistant_lock:
            if self._assistant is None:
                if not self._is_initializing and (self._initialization_thread is None or not self._initialization_thread.is_alive()):
                    logger.info("Initializing AI Assistant (this may take a moment)...")
                    self.start_initialization()
                    # Return None for now, next call will get the initialized assistant
                    return None
            return self._assistant
    
    def start_initialization(self):
        """Start assistant initialization in background thread with improved thread safety"""
        with self._assistant_lock:
            if self._is_initializing or self._assistant is not None:
                # Already initializing or initialized
                return
                
            self._is_initializing = True
            logger.info("Starting AI assistant initialization in background...")
            self._initialization_thread = threading.Thread(target=self._initialize_assistant)
            self._initialization_thread.daemon = True
            self._initialization_thread.start()
    
    def _initialize_assistant(self):
        """Initialize the assistant in a background thread with error handling"""
        try:
            logger.info("Starting AI initialization...")
            with self._assistant_lock:
                # Use AIWrapper with subprocess approach
                self._assistant = AIWrapper(model_path=self.model_path)
                logger.info("AI initialization complete!")
                
        except Exception as e:
            logger.error(f"Error initializing AI: {e}")
            traceback.print_exc()
            self._initialization_error = str(e)
        finally:
            self._is_initializing = False
    
    def _should_process_request(self, message, conversation_id, user_id):
        """Check if this request should be processed or is a duplicate"""
        with self._request_lock:
            current_time = time.time()
            
            # Create a unique key for this request
            request_key = f"{user_id}:{conversation_id}:{message}"
            
            # Check if we've seen this exact request recently
            if request_key in self._request_history:
                last_time = self._request_history[request_key]
                time_diff = current_time - last_time
                
                # If the same request came in too quickly, consider it a duplicate
                if time_diff < self._request_cooldown:
                    logger.warning(f"Duplicate request detected: '{message}' (time diff: {time_diff:.2f}s)")
                    return False
            
            # Update the request history
            self._request_history[request_key] = current_time
            
            # Clean up old entries
            self._clean_request_history()
            
            return True
    
    def _clean_request_history(self):
        """Clean up old request history entries"""
        current_time = time.time()
        keys_to_remove = []
        
        for key, timestamp in self._request_history.items():
            if current_time - timestamp > 60:  # Remove entries older than 1 minute
                keys_to_remove.append(key)
                
        for key in keys_to_remove:
            del self._request_history[key]
    
    def _get_fallback_response(self, message):
        """Provide fallback responses when AI is not available"""
        message_lower = message.lower()
        
        if "library" in message_lower and "hour" in message_lower:
            return "Most UF libraries are open from 7am to 2am on weekdays, with reduced hours on weekends. You can check the UF Libraries website for specific library hours."
            
        elif "event" in message_lower:
            return "For information about UF events, I recommend checking the official UF calendar at calendar.ufl.edu."
            
        elif any(word in message_lower for word in ["who are you", "what are you", "your name"]):
            return "I'm the UF Assistant, an AI designed to assist with any questions or concerns you may have about the University of Florida."
            
        else:
            return "I'm still initializing my AI capabilities. This might take a few minutes. In the meantime, I can provide basic information about UF libraries, buildings, and services."
    
    def process_message(self, message, conversation_id, user_id):
        """Process a user message and store both message and response in the database with deduplication"""
        # Delayed import to prevent circular imports
        from database_tables import db, Message
        
        # Generate a unique request ID for tracking
        request_id = str(uuid.uuid4())
        
        logger.info(f"AI processing message: '{message}' for conversation {conversation_id}, user {user_id}, request ID {request_id}")
        
        # Check for duplicate request
        if not self._should_process_request(message, conversation_id, user_id):
            return "Your previous request is still being processed. Please wait a moment before sending the same message again."
        
        # Generate AI response
        ai_response = ""
        
        # Use full AI if available
        if self._assistant is not None:
            try:
                logger.info(f"Using AI assistant to generate response for request ID {request_id}")
                ai_response = self._assistant.process_query(message, request_id)
                logger.info(f"AI Response: {ai_response[:100]}...")  # Log first 100 chars of response
            except Exception as e:
                logger.error(f"Error generating AI response: {e}")
                traceback.print_exc()
                ai_response = self._get_fallback_response(message)
        else:
            logger.info("AI not yet initialized, using fallback response")
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
            logger.info(f"Successfully saved messages to database for request ID {request_id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving messages: {str(e)}")
            traceback.print_exc()
        
        return ai_response
    
    def get_initialization_status(self):
        """Get the current initialization status"""
        with self._assistant_lock:
            if self._assistant is not None:
                return "ready"
            elif self._is_initializing:
                return "initializing"
            elif self._initialization_error:
                return f"error: {self._initialization_error}"
            else:
                return "not_started"

# Create a singleton instance
ai_manager = AIManager()

# Start initialization immediately
ai_manager.start_initialization()