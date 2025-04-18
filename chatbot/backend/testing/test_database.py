# backend/testing/test_database.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import datetime
from database_tables import User, Conversation, Message

def test_create_user(session):
    user = User(email="test@example.com", password_hash="hashedpass", name="Test User")
    session.add(user)
    session.commit()
    assert user.id is not None

def test_create_conversation(session):
    user = User(email="conv@example.com", password_hash="hash", name="User")
    session.add(user)
    session.commit()
    conv = Conversation(user_id=user.id)
    session.add(conv)
    session.commit()
    assert conv.user_id == user.id

def test_create_message(session):
    user = User(email="msg@example.com", password_hash="pass", name="Msg User")
    session.add(user)
    session.commit()
    conv = Conversation(user_id=user.id)
    session.add(conv)
    session.commit()
    msg = Message(conversation_id=conv.id, user_id=user.id, text="Ahoy, gator fans!")
    session.add(msg)
    session.commit()
    assert msg.text == "Ahoy, gator fans!"
