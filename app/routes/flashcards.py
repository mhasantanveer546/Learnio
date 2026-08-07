from flask import Blueprint, render_template, jsonify, abort, current_app, request
from flask_login import login_required, current_user

from app.models import StudyMaterial, Flashcard
from app.services.flashcard_service import generate_flashcards, mark_card

flashcards_bp = Blueprint("flashcards", __name__, url_prefix="/flashcards")


@flashcards_bp.route("/<int:material_id>/generate", methods=["POST"])
@login_required
def generate_flashcards_route(material_id):
    """Same async pattern as summaries/quizzes: fetch() from the
    subject detail page, returns JSON, no redirect."""
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    if material.status != "ready":
        return jsonify({
            "error": "This material's text hasn't finished processing yet."
        }), 400

    try:
        flashcard_set = generate_flashcards(material)
        return jsonify({"status": flashcard_set.status})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        current_app.logger.warning(f"Flashcard generation failed for material {material_id}: {e}")
        return jsonify({"status": "failed"}), 500


@flashcards_bp.route("/<int:material_id>/status", methods=["GET"])
@login_required
def flashcard_status(material_id):
    """Polled by the frontend while a set is 'processing'."""
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    if not material.flashcard_set:
        return jsonify({"status": "pending"})

    return jsonify({"status": material.flashcard_set.status})


@flashcards_bp.route("/<int:material_id>", methods=["GET"])
@login_required
def study_flashcards(material_id):
    """Renders the flip-card study view — only reachable once
    generation has actually completed."""
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    if not material.flashcard_set or material.flashcard_set.status != "ready":
        abort(404)

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