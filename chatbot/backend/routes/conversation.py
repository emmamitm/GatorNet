from flask import Blueprint, request, jsonify
from database_tables import db, Conversation

conversation_routes = Blueprint('conversation_routes', __name__)

@conversation_routes.route('/conversations/<int:user_id>', methods=['GET'])
def get_conversations_by_user_id(user_id):
    conversations = Conversation.query.filter_by(user_id=user_id).all()
    if not conversations:
        return jsonify({'message': 'No conversations found.'}), 404

    result = []
    for conversation in conversations:
        result.append({
            'id': conversation.id,
            'user_id': conversation.user_id,
            'created_at': conversation.created_at,
            'active' : conversation.active
        })

    return jsonify(result)

@conversation_routes.route('/conversations', methods=['POST'])
def create_conversation():
    data = request.json
    new_conversation = Conversation(
        user_id=data['user_id'],
        created_at=data['created_at'],
        active=data['active']
    )
    db.session.add(new_conversation)
    db.session.commit()
    return jsonify({'success': True, 'conversation_id': new_conversation.id})

