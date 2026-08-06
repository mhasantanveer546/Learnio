import json

from flask import current_app

from app.extensions import db
from app.models import ChatSession, ChatMessage
from app.ai.context_builder import chunk_text
from app.ai.vector_store import add_material_to_index
from app.ai.rag import answer_question


def index_material(material):
    """Chunks a material's extracted text and adds it to its subject's
    FAISS index. Called automatically right after text extraction
    succeeds — same trigger point as status flipping to 'ready' in
    Phase 3's process_material route."""
    if not material.extracted_text:
        return

    chunks = chunk_text(material.extracted_text)
    faiss_folder = current_app.config["FAISS_INDEX_FOLDER"]

    add_material_to_index(
        faiss_folder, material.subject_id, material.id, material.original_name, chunks
    )


def get_or_create_session(subject_id, user_id):
    session = ChatSession.query.filter_by(subject_id=subject_id, user_id=user_id).first()
    if not session:
        session = ChatSession(subject_id=subject_id, user_id=user_id)
        db.session.add(session)
        db.session.commit()
    return session


def send_message(session, question):
    """Saves the user's message, runs the RAG pipeline, saves and
    returns the assistant's reply."""
    user_message = ChatMessage(session_id=session.id, role="user", content=question)
    db.session.add(user_message)
    db.session.commit()

    faiss_folder = current_app.config["FAISS_INDEX_FOLDER"]
    result = answer_question(faiss_folder, session.subject_id, question)

    assistant_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=result["answer"],
        sources=json.dumps(result["sources"]),
    )
    db.session.add(assistant_message)
    db.session.commit()

    return assistant_message