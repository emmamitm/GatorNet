from flask_sqlalchemy import SQLAlchemy
import datetime
import os
from sqlalchemy.orm import relationship
from sqlalchemy import event

db = SQLAlchemy()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AVATAR_DIR = os.path.join(BASE_DIR, "static/avatars")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())
    avatar_path = db.Column(db.String(240), nullable=True)

    conversations = relationship("Conversation", backref="user", cascade="all, delete-orphan")
    messages = relationship("Message", backref="user", cascade="all, delete-orphan")

    @property
    def __repr__(self):
        return f"<User {self.email}>"


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())
    active = db.Column(db.Boolean, nullable=False, default=True)

    messages = relationship("Message", backref="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation {self.id}>"


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey("conversation.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    text = db.Column(db.String(500), nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    def __repr__(self):
        return f"<Message {self.text}>"