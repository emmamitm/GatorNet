# GatorNet/chatbot/backend/app.py

from flask import Flask, request
from flask_cors import CORS
from database_tables import db
from config import Config
from routes.user import user_routes
from routes.chat import chat_routes
from routes.conversation import conversation_routes
from routes.message import message_routes
from routes.login import login_routes
from routes.signup import signup_routes
from ai_integration import ai_manager
from ensure_ai_user import ensure_ai_user_exists

app = Flask(__name__)
CORS(
    app,
    origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)
# Load Configurations
app.config.from_object(Config)
# Secret Key for token generation
# TODO: change to environment variable in production
app.config["secret_key"] = (
    "a6b6831eba9b404d716194f94161cc9376b0270045138623a76f74a4d6781663"
)
# Init Database
db.init_app(app)
# Blueprints
app.register_blueprint(user_routes)
app.register_blueprint(chat_routes)
app.register_blueprint(conversation_routes)
app.register_blueprint(message_routes)
app.register_blueprint(login_routes)
app.register_blueprint(signup_routes)

@app.route("/")
def home():
    return "Chatbot backend is running!"

@app.after_request
def after_request(response):
    print(f"Request to {request.path}: {response.status}")  # Debug print
    return response

if __name__ == "__main__":
    print("Server starting on http://localhost:5001")
    with app.app_context():
        # db.drop_all() // in case of changes in db schema
        db.create_all()
        
        # Ensure AI user exists
        ensure_ai_user_exists()
        
        # Start AI initialization in background
        print("Starting AI assistant initialization in background...")
        ai_manager.start_initialization()
        
        app.run(debug=True, port=5001)