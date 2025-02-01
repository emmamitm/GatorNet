# backend/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import datetime


app = Flask(__name__)
CORS(app)


############Database############


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AVATARS_DIR = os.path.join(BASE_DIR, "avatars")
db_path = os.path.join(BASE_DIR, "database.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())
    avatar = db.Column(db.String(255), nullable=False, default = 'avatars/default.png') #stores the path to the avatar image

    def __repr__(self):
        return '<User %r>' % self.email

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())
    active = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return '<Conversation %r>' % self.id

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    def __repr__(self):
        return '<Message %r>' % self.text


with app.app_context():
    db.create_all()



################################

@app.route('/')
def home():
    return "Chatbot backend is running!"

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