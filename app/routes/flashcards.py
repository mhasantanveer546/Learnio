from flask import Blueprint, render_template, jsonify, abort, current_app, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import limiter, db
from app.models import StudyMaterial, Flashcard, FlashcardSet
from app.services.flashcard_service import generate_flashcards, mark_card
from app.services.background_ai import run_background_task

flashcards_bp = Blueprint("flashcards", __name__, url_prefix="/flashcards")


@flashcards_bp.route("/<int:material_id>/generate", methods=["POST"])
@limiter.limit("3 per minute")
@login_required
def generate_flashcards_route(material_id):
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    if not material.extracted_text:
        flash("This material has no extracted text yet.", "warning")
        return redirect(url_for("flashcards.study_flashcards", material_id=material_id))

    existing = FlashcardSet.query.filter_by(material_id=material_id).first()
    if existing:
        for card in list(existing.cards):
            db.session.delete(card)
        db.session.delete(existing)
        db.session.commit()

    flashcard_set = FlashcardSet(material_id=material_id, status="processing")
    db.session.add(flashcard_set)
    db.session.commit()

    num_cards = request.form.get("num_cards", 15, type=int)

    # Pass ID only — ORM objects are bound to the request session
    run_background_task(generate_flashcards, material_id=material.id, num_cards=num_cards)

    flash("Flashcard generation started!", "info")
    return redirect(url_for("flashcards.study_flashcards", material_id=material_id))


@flashcards_bp.route("/<int:material_id>/status")
@login_required
def flashcard_status(material_id):
    flashcard_set = FlashcardSet.query.filter_by(material_id=material_id).first_or_404()
    if flashcard_set.material.user_id != current_user.id:
        abort(403)
    return jsonify({"status": flashcard_set.status})


@flashcards_bp.route("/<int:material_id>", methods=["GET"])
@login_required
def study_flashcards(material_id):
    """Renders the study view for any status — polling handles processing/failed."""
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    return render_template(
        "flashcards/study.html", material=material, flashcard_set=material.flashcard_set
    )


@flashcards_bp.route("/card/<int:card_id>/mark", methods=["POST"])
@login_required
def mark_card_route(card_id):
    """AJAX endpoint the study view calls on every flip/rating —
    ownership verified by joining through the material, same pattern
    as self_grade_route in quizzes.py."""
    card = Flashcard.query.join(Flashcard.flashcard_set).join(StudyMaterial).filter(
        Flashcard.id == card_id, StudyMaterial.user_id == current_user.id
    ).first_or_404()

    data = request.get_json() or {}
    try:
        card = mark_card(card, is_learned=data.get("is_learned"), difficulty=data.get("difficulty"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "id": card.id,
        "is_learned": card.is_learned,
        "difficulty": card.difficulty,
        "learned_count": card.flashcard_set.learned_count,
        "total": len(card.flashcard_set.cards),
    })