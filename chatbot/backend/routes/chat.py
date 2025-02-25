# GatorNet/chatbot/backend/routes/chat.py

from flask import Blueprint, request, jsonify
from ai_integration import ai_manager
from database_tables import db, Conversation, Message
from datetime import datetime

chat_routes = Blueprint('chat_routes', __name__)

@chat_routes.route('/api/chat', methods=['POST'])
def chat():
    try:
        print("Received message:", request.json)  # Debug print
        
        # Extract data from request
        message = request.json.get('message', '')
        user_id = request.json.get('user_id')
        conversation_id = request.json.get('conversation_id')
        
        # If user_id is missing, use default
        if not user_id:
            user_id = 1
        
        # Find or create a conversation for this user
        if not conversation_id:
            # First try to find an active conversation with less than 10 messages
            active_conversations = Conversation.query.filter_by(
                user_id=user_id,
                active=True
            ).all()
            
            valid_conversation = None
            
            for conv in active_conversations:
                message_count = Message.query.filter_by(conversation_id=conv.id).count()
                if message_count < 10:
                    valid_conversation = conv
                    break
            
            # If no valid conversation found, create a new one
            if not valid_conversation:
                # First mark all previous conversations as inactive
                for conv in active_conversations:
                    conv.active = False
                
                # Create a new conversation
                valid_conversation = Conversation(
                    user_id=user_id,
                    started_at=datetime.now(),
                    active=True
                )
                db.session.add(valid_conversation)
                db.session.commit()
                print(f"Created new conversation: {valid_conversation.id}")
            
            conversation_id = valid_conversation.id
            print(f"Using conversation: {conversation_id}")
        
        # Check message count in the conversation
        message_count = Message.query.filter_by(conversation_id=conversation_id).count()
        
        # If already at 10 messages, create a new conversation
        if message_count >= 10:
            # Mark current conversation as inactive
            current_conversation = Conversation.query.get(conversation_id)
            if current_conversation:
                current_conversation.active = False
            
            # Create a new conversation
            new_conversation = Conversation(
                user_id=user_id,
                started_at=datetime.now(),
                active=True
            )
            db.session.add(new_conversation)
            db.session.commit()
            
            conversation_id = new_conversation.id
            print(f"Reached 10 message limit. Created new conversation: {conversation_id}")
        
        # Process with AI and get response
        print("Calling AI for response...")
        response = ai_manager.process_message(message, conversation_id, user_id)
        
        print("AI Response:", response)  # Debug print
        return jsonify({
            'response': response,
            'conversation_id': conversation_id
        })
    
    except Exception as e:
        print("Error in /api/chat:", str(e))  # Debug print
        return jsonify({'error': str(e)}), 500