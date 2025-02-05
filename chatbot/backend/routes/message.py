from flask import Blueprint, request, jsonify
from database_tables import db, Message
from datetime import datetime

message_routes = Blueprint('message_routes', __name__)

@message_routes.route('/api/conversations/<int:conversation_id>/messages_active', methods=['GET'])
def get_messages(conversation_id):
    messages = Message.query.filter_by(conversation_id=conversation_id).all()
    return jsonify([{
        'text': message.text,
        'sent_at': message.sent_at
    } for message in messages])

@message_routes.route('/api/conversations/<int:conversation_id>/messages', methods=['POST'])
def post_message(conversation_id):
    data = request.json
    new_message = Message(
        conversation_id=conversation_id,
        user_id=data['user_id'],
        text=data['text'],
        sent_at=datetime.now()
    )
    db.session.add(new_message)
    db.session.commit()
    return jsonify({'success': True, 'message_id': new_message.id})