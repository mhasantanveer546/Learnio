import json

from app.extensions import db
from app.models import ChatSession, ChatMessage
from app.ai.context_builder import chunk_text
from app.ai.vector_store import build_material_index, delete_material_index
from app.ai.rag import answer_question


def index_material(material):
    if not material.extracted_text:
        return
    chunks = chunk_text(material.extracted_text)
    build_material_index(material.id, material.original_name, chunks)


def remove_material_index(material):
    delete_material_index(material.id)


def get_or_create_session(material_id, user_id):
    session = ChatSession.query.filter_by(material_id=material_id, user_id=user_id).first()
    if not session:
        session = ChatSession(material_id=material_id, user_id=user_id)
        db.session.add(session)
        db.session.commit()
    return session


def send_message(session, question, mode="study"):
    user_message = ChatMessage(session_id=session.id, role="user", content=question)
    db.session.add(user_message)
    db.session.commit()

    result = answer_question(session.material_id, question, mode=mode)

    assistant_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=result["answer"],
        sources=json.dumps(result["sources"]),
    )
    db.session.add(assistant_message)
    db.session.commit()

    return assistant_message