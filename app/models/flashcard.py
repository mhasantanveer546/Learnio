from datetime import datetime, timezone

from app.extensions import db


class FlashcardSet(db.Model):
    __tablename__ = "flashcard_sets"

    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(
        db.Integer, db.ForeignKey("study_materials.id"), nullable=False, unique=True, index=True
    )

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
        backref=db.backref("flashcard_set", uselist=False, cascade="all, delete-orphan"),
    )
    cards = db.relationship(
        "Flashcard", backref="flashcard_set", lazy=True, cascade="all, delete-orphan",
        order_by="Flashcard.order_index",
    )

    @property
    def learned_count(self):
        return sum(1 for c in self.cards if c.is_learned)

    def __repr__(self):
        return f"<FlashcardSet for material {self.material_id}>"


class Flashcard(db.Model):
    __tablename__ = "flashcards"

    id = db.Column(db.Integer, primary_key=True)
    set_id = db.Column(db.Integer, db.ForeignKey("flashcard_sets.id"), nullable=False, index=True)

    front_text = db.Column(db.Text, nullable=False)
    back_text = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(10), nullable=False, default="new")  # new/easy/medium/hard
    is_learned = db.Column(db.Boolean, nullable=False, default=False)
    order_index = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Flashcard {self.id} ({self.difficulty})>"