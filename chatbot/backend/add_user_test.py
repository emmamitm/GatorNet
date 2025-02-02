from app import app, db, User, Conversation, Message
from werkzeug.security import generate_password_hash

users = [
    {
        "email": "gatornet@ufl.edu", "password": "password", "avatar": "1.png"
    },
    {
        "email": "testuser@ufl.edu", "password": "password", "avatar": "2.png"
    }
]

with app.app_context():
    for user in users:
        new_user = User(email=user["email"], password_hash=generate_password_hash(user["password"]), avatar=user["avatar"])
        db.session.add(new_user)
        db.session.commit()
