from datetime import datetime, timezone

from app.extensions import db


class Summary(db.Model):
    __tablename__ = "summaries"

    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(
        db.Integer, db.ForeignKey("study_materials.id"), nullable=False, unique=True, index=True
    )

    content = db.Column(db.Text, nullable=True)  # structured Markdown; null until generation completes
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending/processing/ready/failed

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    material = db.relationship(
        "StudyMaterial",
        backref=db.backref("summary", uselist=False, cascade="all, delete-orphan"),
    )

    def __repr__(self):
        return f"<Summary for material {self.material_id}>"