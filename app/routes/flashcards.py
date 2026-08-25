from datetime import datetime, timezone
from flask import Blueprint, render_template, jsonify, abort, current_app, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import limiter, db
from app.models import StudyMaterial, Flashcard, FlashcardSet
from app.services.flashcard_service import generate_flashcards, mark_card
from app.services.background_ai import run_background_task


def _elapsed_seconds(created_at):
    """Safely compute elapsed time since created_at, handling both
    timezone-aware and naive datetimes from the database."""
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return (now - created_at).total_seconds()


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
        if existing.status == "ready":
            flash("Flashcards already exist for this material.", "info")
            return redirect(url_for("flashcards.study_flashcards", material_id=material_id))

        if existing.status == "processing":
            elapsed = _elapsed_seconds(existing.created_at)
            if elapsed < 30:
                flash("Flashcard generation is already in progress. Please wait.", "info")
                return redirect(url_for("flashcards.study_flashcards", material_id=material_id))

        for card in list(existing.cards):
            db.session.delete(card)
        db.session.delete(existing)
        db.session.commit()

    flashcard_set = FlashcardSet(material_id=material_id, status="processing")
    db.session.add(flashcard_set)
    db.session.commit()

    num_cards = request.form.get("num_cards", 15, type=int)

    try:
        generate_flashcards(material_id=material.id, num_cards=num_cards)
        flash("Flashcards generated successfully!", "success")
    except Exception as e:
        current_app.logger.exception(f"Flashcard generation failed: {e}")
        flash("Flashcard generation failed. Please try again.", "danger")

    return redirect(url_for("flashcards.study_flashcards", material_id=material_id))

@flashcards_bp.route("/<int:material_id>/status")
@login_required
def flashcard_status(material_id):
    flashcard_set = FlashcardSet.query.filter_by(material_id=material_id).first_or_404()
    if flashcard_set.material.user_id != current_user.id:
        abort(403)

    if flashcard_set.status == "processing":
        elapsed = _elapsed_seconds(flashcard_set.created_at)
        if elapsed > 180:
            flashcard_set.status = "failed"
            db.session.commit()

    return jsonify({"status": flashcard_set.status})


@flashcards_bp.route("/<int:material_id>", methods=["GET"])
@login_required
def study_flashcards(material_id):
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    resp = render_template(
        "flashcards/study.html", material=material, flashcard_set=material.flashcard_set
    )
    resp = make_response(resp)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

@flashcards_bp.route("/card/<int:card_id>/mark", methods=["POST"])
@login_required
def mark_card_route(card_id):
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