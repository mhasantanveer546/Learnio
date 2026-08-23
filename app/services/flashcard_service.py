import json

from app.extensions import db
from app.models import StudyMaterial, FlashcardSet, Flashcard
from app.ai.client import generate_content
from app.ai.prompts import build_flashcard_prompt


def _validate_flashcard_json(parsed):
    """Defensive validation: don't trust AI output blindly."""
    if not isinstance(parsed, dict):
        raise ValueError(f"Expected JSON object, got {type(parsed).__name__}")

    if "flashcards" not in parsed:
        raise ValueError("Missing 'flashcards' key")

    if not isinstance(parsed["flashcards"], list):
        raise ValueError(
            f"Expected 'flashcards' to be a list, got {type(parsed['flashcards']).__name__}"
        )

    for i, card in enumerate(parsed["flashcards"]):
        if not isinstance(card, dict):
            raise ValueError(f"Flashcard {i} is not an object")

        if "front" not in card or "back" not in card:
            raise ValueError(f"Flashcard {i} missing 'front' or 'back'")

    return parsed


def generate_flashcards(material_id, num_cards=15):
    """Generates (or regenerates) a flashcard set from a material's
    extracted text. Re-queries the material in the background thread's
    fresh session so lazy loading works."""

    material = db.session.get(StudyMaterial, material_id)
    if material is None or not material.extracted_text:
        raise ValueError("This material has no extracted text yet.")

    flashcard_set = material.flashcard_set
    if flashcard_set is None:
        flashcard_set = FlashcardSet(material_id=material.id, status="processing")
        db.session.add(flashcard_set)
    else:
        flashcard_set.status = "processing"
        for card in list(flashcard_set.cards):
            db.session.delete(card)
    db.session.commit()

    prompt = build_flashcard_prompt(material.extracted_text, num_cards)

    try:
        raw_response = generate_content(prompt)
        cleaned = (
            raw_response.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        parsed = json.loads(cleaned)
        parsed = _validate_flashcard_json(parsed)

        for index, c in enumerate(parsed["flashcards"]):
            card = Flashcard(
                set_id=flashcard_set.id,
                front_text=c["front"],
                back_text=c["back"],
                order_index=index,
            )
            db.session.add(card)

        flashcard_set.status = "ready"
        db.session.commit()

    except (json.JSONDecodeError, KeyError, ValueError, RuntimeError) as e:
        flashcard_set.status = "failed"
        db.session.commit()
        raise RuntimeError(f"Flashcard generation failed: {e}")

    return flashcard_set


def mark_card(card, is_learned=None, difficulty=None):
    """Updates a single card's review state. Called from the study
    view whenever the student flips + rates a card — kept as a small
    targeted update rather than resaving the whole set."""
    if is_learned is not None:
        card.is_learned = is_learned
    if difficulty is not None:
        if difficulty not in ("new", "easy", "medium", "hard"):
            raise ValueError("Invalid difficulty value.")
        card.difficulty = difficulty

    db.session.commit()
    return card