import json

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user

from app.models import StudyMaterial
from app.services.chat_service import get_or_create_session, send_message

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.route("/<int:material_id>", methods=["GET"])
@login_required
def view_chat(material_id):
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    chat_session = get_or_create_session(material.id, current_user.id)

    return render_template(
        "ai_chat/chat.html",
        material=material,
        chat_session=chat_session,
        messages=chat_session.messages,
    )


@chat_bp.route("/<int:material_id>/send", methods=["POST"])
@login_required
def send_message_route(material_id):
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    chat_session = get_or_create_session(material.id, current_user.id)

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid request."}), 400

    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Question cannot be empty."}), 400

    mode = data.get("mode", "study")
    if mode not in ("study", "solve"):
        mode = "study"  # defensive fallback — never trust client input blindly

    try:
        assistant_message = send_message(chat_session, question, mode=mode)
        return jsonify({
            "reply": assistant_message.content,
            "sources": json.loads(assistant_message.sources) if assistant_message.sources else [],
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        current_app.logger.exception(f"Chat generation failed for material {material.id}: {e}")
        return jsonify({"error": "Failed to generate a response."}), 500