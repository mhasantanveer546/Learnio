from datetime import datetime, timezone

from app.extensions import db


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(7), nullable=False, default="#2563EB")  # hex, defaults to primary blue
    icon = db.Column(db.String(50), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Reverse relationship — lets you do current_user.subjects to get all
    # of a user's subjects without writing a manual query every time.
    # cascade="all, delete-orphan" means: if a User row is deleted, all
    # their Subjects go with it automatically at the ORM level.
    owner = db.relationship("User", backref=db.backref("subjects", lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Subject {self.name}>"