from datetime import datetime, timezone

from app.extensions import db


class StudySession(db.Model):
    __tablename__ = "study_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=True, index=True)  # NULL = general study

    started_at = db.Column(db.DateTime, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)  # set once the session ends
    completed = db.Column(db.Boolean, nullable=False, default=False)  # True = ran the full focus period

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    owner = db.relationship("User", backref=db.backref("study_sessions", lazy=True, cascade="all, delete-orphan"))
    subject = db.relationship("Subject", backref=db.backref("study_sessions", lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<StudySession {self.id} user={self.user_id}>"