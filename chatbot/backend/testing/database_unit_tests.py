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

def test_user_unique_email(session):
    user1 = User(email="unique@example.com", password_hash="pass1", name="User1")
    session.add(user1)
    session.commit()
    user2 = User(email="unique@example.com", password_hash="pass2", name="User2")
    session.add(user2)
    try:
        session.commit()
        assert False, "Duplicate email allowed"
    except Exception:
        session.rollback()

def test_conversation_without_user(session):
    conv = Conversation(user_id=None)
    session.add(conv)
    try:
        session.commit()
        assert False, "Conversation without user allowed"
    except Exception:
        session.rollback()

def test_message_without_conversation(session):
    user = User(email="msg2@example.com", password_hash="pass", name="Msg User 2")
    session.add(user)
    session.commit()
    msg = Message(conversation_id=None, user_id=user.id, text="Message without conversation")
    session.add(msg)
    try:
        session.commit()
        assert False, "Message without conversation allowed"
    except Exception:
        session.rollback()

def test_message_without_user(session):
    user = User(email="tempuser@example.com", password_hash="pass", name="Temp User")
    session.add(user)
    session.commit()
    conv = Conversation(user_id=user.id)
    session.add(conv)
    session.commit()
    msg = Message(conversation_id=conv.id, user_id=None, text="Message without user")
    session.add(msg)
    try:
        session.commit()
        assert False, "Message without user allowed"
    except Exception:
        session.rollback()

def test_delete_user_cascade_conversations(session):
    user = User(email="cascade@example.com", password_hash="pass", name="Cascade User")
    session.add(user)
    session.commit()
    conv = Conversation(user_id=user.id)
    session.add(conv)
    session.commit()
    session.delete(user)
    session.commit()
    deleted_conv = session.query(Conversation).filter_by(id=conv.id).first()
    assert deleted_conv is None

def test_delete_conversation_cascade_messages(session):
    user = User(email="cascade2@example.com", password_hash="pass", name="Cascade User 2")
    session.add(user)
    session.commit()
    conv = Conversation(user_id=user.id)
    session.add(conv)
    session.commit()
    msg = Message(conversation_id=conv.id, user_id=user.id, text="Cascade message")
    session.add(msg)
    session.commit()
    session.delete(conv)
    session.commit()
    deleted_msg = session.query(Message).filter_by(id=msg.id).first()
    assert deleted_msg is None