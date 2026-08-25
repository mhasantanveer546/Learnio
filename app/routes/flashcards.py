from datetime import datetime, timezone
from time import time
from flask import Blueprint, render_template, jsonify, abort, current_app, request, flash, redirect, url_for, make_response
from flask_login import login_required, current_user
from app.extensions import limiter, db
from app.models import StudyMaterial, Flashcard, FlashcardSet
from app.services.flashcard_service import generate_flashcards, mark_card


def _elapsed_seconds(created_at):
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
        return jsonify({"status": "failed", "error": "No extracted text yet"}), 400

    existing = FlashcardSet.query.filter_by(material_id=material_id).first()

    if existing:
        if existing.status == "ready":
            return jsonify({"status": "ready"})

        if existing.status == "processing":
            elapsed = _elapsed_seconds(existing.created_at)
            if elapsed < 30:
                return jsonify({"status": "processing"})

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
        db.session.refresh(flashcard_set)
        return jsonify({"status": flashcard_set.status})
    except Exception as e:
        current_app.logger.exception(f"Flashcard generation failed: {e}")
        db.session.refresh(flashcard_set)
        return jsonify({"status": "failed", "error": str(e)}), 500


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

    resp = jsonify({"status": flashcard_set.status})
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@flashcards_bp.route("/<int:material_id>", methods=["GET"])
@login_required
def study_flashcards(material_id):
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    resp = make_response(render_template(
        "flashcards/study.html", material=material, flashcard_set=material.flashcard_set
    ))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
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