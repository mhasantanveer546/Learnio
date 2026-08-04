from datetime import datetime, timezone

from app.extensions import db


class StudyMaterial(db.Model):
    __tablename__ = "study_materials"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    filename = db.Column(db.String(255), nullable=False)        # UUID-based, safe on disk
    original_name = db.Column(db.String(255), nullable=False)   # display only, never used as a path
    file_type = db.Column(db.String(10), nullable=False)        # pdf, docx, pptx, txt, jpg, png
    file_size = db.Column(db.Integer, nullable=False)           # bytes

    extracted_text = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending/processing/ready/failed

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    subject = db.relationship(
        "Subject",
        backref=db.backref("materials", lazy=True, cascade="all, delete-orphan"),
    )
    owner = db.relationship(
        "User",
        backref=db.backref("materials", lazy=True, cascade="all, delete-orphan"),
    )

    def __repr__(self):
        return f"<StudyMaterial {self.original_name}>"