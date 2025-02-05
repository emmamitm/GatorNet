# backend/app.py
from flask import Flask, request
from flask_cors import CORS
from database_tables import db
from config import Config
from routes.user import user_routes
from routes.chat import chat_routes
from routes.conversation import conversation_routes
from routes.message import message_routes


app = Flask(__name__)
CORS(app)

# Load Configurations
app.config.from_object(Config)

# Init Database
db.init_app(app)

# Blueprints
app.register_blueprint(user_routes)
app.register_blueprint(chat_routes)
app.register_blueprint(conversation_routes)
app.register_blueprint(message_routes)

@app.route('/')
def home():
    return "Chatbot backend is running!"

@app.after_request
def after_request(response):
    print(f"Request to {request.path}: {response.status}")  # Debug print
    return response

if __name__ == '__main__':
    print("Server starting on http://localhost:5001")
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)