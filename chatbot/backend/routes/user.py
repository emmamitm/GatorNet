from flask import Blueprint, request, jsonify
from database_tables import db, User
from werkzeug.security import generate_password_hash

user_routes = Blueprint('user_routes', __name__)

@user_routes.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.email for user in users])

@user_routes.route('/api/users', methods=['POST'])
def add_user():
    try:
        data = request.json
        new_user = User(
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            avatar=data.get('avatar', 'default.png')
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'success': True, 'user_id': new_user.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_routes.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if user:
        return jsonify({'email': user.email, 'avatar': user.avatar})
    return jsonify({'error': 'User not found'}), 404

@user_routes.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'User not found'}), 404

@user_routes.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    if user:
        data = request.json
        user.email = data.get('email', user.email)
        user.password_hash = data.get('password', user.password_hash)
        user.avatar = data.get('avatar', user.avatar)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'User not found'}), 404