# backend/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os


app = Flask(__name__)
CORS(app)


############Database############


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "users.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.email

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