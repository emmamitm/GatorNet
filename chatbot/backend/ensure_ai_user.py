# GatorNet/chatbot/backend/ensure_ai_user.py

from database_tables import db, User
from werkzeug.security import generate_password_hash

def ensure_ai_user_exists():
    """Ensure a special AI user exists in the database with ID 0"""
    try:
        # Check if AI user exists
        ai_user = User.query.filter_by(id=0).first()
        
        if not ai_user:
            print("Creating special AI user...")
            # Create AI user with ID 0
            ai_user = User(
                id=0,
                email="ai@gatornet.internal",
                password_hash=generate_password_hash("not-a-real-password"),
                name="GatorNet AI"
            )
            
            # Explicitly set ID to 0 (this might require disabling SQLAlchemy autoincrement)
            ai_user.id = 0
            
            # Add AI user to database
            db.session.add(ai_user)
            db.session.commit()
            print("AI user created successfully")
            
    except Exception as e:
        print(f"Error ensuring AI user exists: {str(e)}")
        db.session.rollback()