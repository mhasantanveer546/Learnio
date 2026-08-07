import json

from app.extensions import db
from app.models import FlashcardSet, Flashcard
from app.ai.client import generate_content
from app.ai.prompts import build_flashcard_prompt


def generate_flashcards(material, num_cards=15):
    """Generates (or regenerates) a flashcard set from a material's
    extracted text. Mirrors generate_quiz's structure exactly: create
    the parent row as 'processing' first, call Gemini, parse JSON into
    child rows, flip to 'ready' or 'failed'.

    Regeneration replaces all existing cards for this material rather
    than appending — a material has exactly one flashcard set, same
    one-per-material model as Summary."""

    if not material.extracted_text:
        raise ValueError("This material has no extracted text yet.")

    flashcard_set = material.flashcard_set
    if flashcard_set is None:
        flashcard_set = FlashcardSet(material_id=material.id, status="processing")
        db.session.add(flashcard_set)
    else:
        flashcard_set.status = "processing"
        # Regenerating: clear old cards so we don't end up with a mix
        # of two different generations' cards under one set.
        for card in list(flashcard_set.cards):
            db.session.delete(card)
    db.session.commit()

    prompt = build_flashcard_prompt(material.extracted_text, num_cards)

    try:
        raw_response = generate_content(prompt)
        cleaned = raw_response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(cleaned)

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

    except (json.JSONDecodeError, KeyError, RuntimeError) as e:
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