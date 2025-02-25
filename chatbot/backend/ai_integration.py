# GatorNet/chatbot/backend/ai_integration.py

import sys
import os

# Import the UFAssistant directly from our local copy
from AI.AI_model import UFAssistant
from database_tables import db, Message, Conversation, User
from datetime import datetime
import threading
import time

class AIManager:
    def __init__(self):
        # Initialize the UF Assistant with a lazy loading mechanism
        self._assistant = None
        self._assistant_lock = threading.Lock()
        self._initialization_thread = None

    @property
    def assistant(self):
        """Lazy-load the assistant when first needed"""
        with self._assistant_lock:
            if self._assistant is None:
                if self._initialization_thread is None or not self._initialization_thread.is_alive():
                    print("Initializing UF Assistant (this may take a moment)...")
                    self._assistant = UFAssistant()
            return self._assistant

    def start_initialization(self):
        """Start assistant initialization in background thread"""
        if self._assistant is None and (self._initialization_thread is None or not self._initialization_thread.is_alive()):
            self._initialization_thread = threading.Thread(target=self._initialize_assistant)
            self._initialization_thread.daemon = True
            self._initialization_thread.start()
            
    def _initialize_assistant(self):
        """Initialize the assistant in a background thread"""
        with self._assistant_lock:
            if self._assistant is None:
                self._assistant = UFAssistant()

    def process_message(self, message, conversation_id, user_id):
        """Process a user message and store both message and response in the database"""
        print(f"AI processing message: '{message}' for conversation {conversation_id}, user {user_id}")
        
        # Ensure the assistant is initialized
        print("Getting AI assistant...")
        assistant = self.assistant
        print("AI assistant ready")
        
        # Generate AI response
        ai_response = assistant.generate_response(message)
        
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
        except Exception as e:
            db.session.rollback()
            print(f"Error saving messages: {str(e)}")
        
        return ai_response

# Create a singleton instance
ai_manager = AIManager()