from datetime import datetime

from app.extensions import db


class Summary(db.Model):
    __tablename__ = "summaries"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    title = db.Column(
        db.String(255),
        nullable=False,
    )

    content = db.Column(
        db.Text,
        nullable=False,
    )

    summary_type = db.Column(
        db.String(50),
        nullable=False,
        default="chapter",
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    material_id = db.Column(
        db.Integer,
        db.ForeignKey("study_materials.id"),
        nullable=False,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )

    material = db.relationship(
        "StudyMaterial",
        back_populates="summaries",
    )

    user = db.relationship(
        "User",
        back_populates="summaries",
    )

    def __repr__(self):
        return (
            f"<Summary {self.id}: "
            f"{self.title}>"
        )