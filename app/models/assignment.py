from datetime import datetime, timezone

from app.extensions import db


class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=False, index=True)
    priority = db.Column(db.String(10), nullable=False, default="medium")  # low/medium/high
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending/in_progress/completed

    # Single optional attachment — filename is UUID-based (safe on disk),
    # original_name is what the student uploaded (display only), same
    # split as StudyMaterial's filename/original_name from Phase 3.
    attachment_filename = db.Column(db.String(255), nullable=True)
    attachment_original_name = db.Column(db.String(255), nullable=True)
    attachment_size = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    subject = db.relationship("Subject", backref=db.backref("assignments", lazy=True, cascade="all, delete-orphan"))
    owner = db.relationship("User", backref=db.backref("assignments", lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Assignment {self.title}>"


class Exam(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    exam_date = db.Column(db.DateTime, nullable=False, index=True)
    location = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    subject = db.relationship("Subject", backref=db.backref("exams", lazy=True, cascade="all, delete-orphan"))
    owner = db.relationship("User", backref=db.backref("exams", lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Exam {self.title}>"