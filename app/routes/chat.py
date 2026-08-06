import json

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user

from app.models import Subject
from app.services.chat_service import get_or_create_session, send_message

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.route("/<int:subject_id>", methods=["GET"])
@login_required
def view_chat(subject_id):
    """Display the AI chat page for a subject. Creates a chat session
    automatically if one doesn't exist yet."""
    subject = Subject.query.filter_by(
        id=subject_id, user_id=current_user.id
    ).first_or_404()

    chat_session = get_or_create_session(subject.id, current_user.id)

    return render_template(
        "ai_chat/chat.html",
        subject=subject,
        chat_session=chat_session,
        messages=chat_session.messages,
    )


@chat_bp.route("/<int:subject_id>/send", methods=["POST"])
@login_required
def send_message_route(subject_id):
    """Receives a user question via fetch(), sends it through the RAG
    pipeline, and returns the assistant's response as JSON."""
    subject = Subject.query.filter_by(
        id=subject_id, user_id=current_user.id
    ).first_or_404()

    chat_session = get_or_create_session(subject.id, current_user.id)

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid request."}), 400

    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Question cannot be empty."}), 400

    try:
        assistant_message = send_message(chat_session, question)
        return jsonify({
            "reply": assistant_message.content,
            "sources": json.loads(assistant_message.sources) if assistant_message.sources else [],
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        current_app.logger.exception(f"Chat generation failed for subject {subject.id}: {e}")
        return jsonify({"error": "Failed to generate a response."}), 500