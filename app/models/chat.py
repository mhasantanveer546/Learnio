from datetime import datetime, timezone

from app.extensions import db


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    subject = db.relationship("Subject", backref=db.backref("chat_sessions", lazy=True, cascade="all, delete-orphan"))
    owner = db.relationship("User", backref=db.backref("chat_sessions", lazy=True, cascade="all, delete-orphan"))
    messages = db.relationship(
        "ChatMessage", backref="session", lazy=True, cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )

    def __repr__(self):
        return f"<ChatSession {self.id} for subject {self.subject_id}>"


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = db.Column(db.String(10), nullable=False)  # "user" or "assistant"
    content = db.Column(db.Text, nullable=False)
    sources = db.Column(db.Text, nullable=True)  # JSON array of material names cited
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<ChatMessage {self.id} ({self.role})>"