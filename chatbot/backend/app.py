# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from models import *
from werkzeug.security import generate_password_hash


app = Flask(__name__)
CORS(app)


@app.route('/')
def home():
    return "Chatbot backend is running!"

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.email for user in users])

@app.route('/api/users', methods=['POST'])
def add_user():
    try:
        data = request.json
        new_user = User(email=data['email'], password_hash=generate_password_hash(data['password']), avatar=data.get('avatar', 'default.png'))
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if user:
        return jsonify({'email': user.email, 'avatar': user.avatar})
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/users/<int:user_id>', methods=['PUT'])
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

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        print("Received message:", request.json)  # Debug print
        message = request.json.get('message', '')
        response = f"Echo: {message}"
        print("Sending response:", response)  # Debug print
        return jsonify({'response': response})
    except Exception as e:
        print("Error in /api/chat:", str(e))  # Debug print
        return jsonify({'error': str(e)}), 500

@app.after_request
def after_request(response):
    print(f"Request to {request.path}: {response.status}")  # Debug print
    return response

if __name__ == '__main__':
    print("Server starting on http://localhost:5001")
    app.run(debug=True, port=5001)