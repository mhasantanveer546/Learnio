from datetime import datetime, timezone

from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=True)  # where clicking it should go
    is_read = db.Column(db.Boolean, nullable=False, default=False)

    # Identifies WHICH real-world thing this notification is about, so
    # we can check "does a notification for this assignment already
    # exist" without string-matching the message text — that's the
    # actual duplicate-prevention mechanism.
    source_type = db.Column(db.String(20), nullable=False)  # "assignment" or "exam"
    source_id = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    owner = db.relationship("User", backref=db.backref("notifications", lazy=True, cascade="all, delete-orphan"))

    __table_args__ = (
        db.UniqueConstraint("user_id", "source_type", "source_id", name="uq_notification_source"),
    )

    def __repr__(self):
        return f"<Notification {self.id}: {self.message}>"