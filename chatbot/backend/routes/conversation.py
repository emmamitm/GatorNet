# GatorNet/chatbot/backend/routes/conversation.py

from flask import Blueprint, request, jsonify
from database_tables import db, Conversation, Message, User
from datetime import datetime
from auth import token_required

conversation_routes = Blueprint('conversation_routes', __name__)

@conversation_routes.route('/api/conversations', methods=['GET'])
@token_required
def get_user_conversations(current_user):
    """Get all conversations for the current user"""
    try:
        # Query all conversations for the user
        conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.started_at.desc()).all()
        
        result = []
        for conversation in conversations:
            # Get first message to use as title
            first_message = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.sent_at.asc()).first()
            title = "New Conversation"
            if first_message:
                # Limit title length to 30 characters
                title = first_message.text[:30] + ("..." if len(first_message.text) > 30 else "")
            
            # Count messages in conversation
            message_count = Message.query.filter_by(conversation_id=conversation.id).count()
            
            result.append({
                'id': conversation.id,
                'title': title,
                'started_at': conversation.started_at.isoformat(),
                'active': conversation.active,
                'message_count': message_count
            })
        
        return jsonify(result)
    except Exception as e:
        print(f"Error getting conversations: {str(e)}")
        return jsonify({'error': str(e)}), 500

@conversation_routes.route('/api/conversations/<int:conversation_id>/messages', methods=['GET'])
@token_required
def get_conversation_messages(current_user, conversation_id):
    """Get all messages for a specific conversation"""
    try:
        # Verify the conversation belongs to the user
        conversation = Conversation.query.get(conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            return jsonify({'error': 'Conversation not found or access denied'}), 404
        
        # Get all messages for the conversation
        messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.sent_at.asc()).all()
        
        result = []
        for message in messages:
            # Determine if message is from user or AI
            is_user = message.user_id == current_user.id
            
            result.append({
                'id': message.id,
                'text': message.text,
                'sent_at': message.sent_at.isoformat(),
                'isUser': is_user
            })
        
        return jsonify(result)
    except Exception as e:
        print(f"Error getting messages: {str(e)}")
        return jsonify({'error': str(e)}), 500

@conversation_routes.route('/api/conversations/<int:conversation_id>', methods=['DELETE'])
@token_required
def delete_conversation(current_user, conversation_id):
    """Delete a conversation and all its messages"""
    try:
        # Verify the conversation belongs to the user
        conversation = Conversation.query.get(conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            return jsonify({'error': 'Conversation not found or access denied'}), 404
        
        # Delete all messages first
        Message.query.filter_by(conversation_id=conversation_id).delete()
        
        # Then delete the conversation
        db.session.delete(conversation)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error deleting conversation: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@conversation_routes.route('/api/conversations', methods=['POST'])
@token_required
def create_new_conversation(current_user):
    """Create a new empty conversation"""
    try:
        # Create new conversation
        new_conversation = Conversation(
            user_id=current_user.id,
            started_at=datetime.now(),
            active=True
        )
        
        db.session.add(new_conversation)
        db.session.commit()
        
        return jsonify({
            'id': new_conversation.id,
            'title': 'New Conversation',
            'started_at': new_conversation.started_at.isoformat(),
            'active': True,
            'message_count': 0
        })
    except Exception as e:
        print(f"Error creating new conversation: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500