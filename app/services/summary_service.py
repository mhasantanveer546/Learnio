from app.extensions import db
from app.models import StudyMaterial, Summary
from app.ai.client import generate_content
from app.ai.prompts import build_summary_prompt

MAX_TEXT_LENGTH = 15000  # ~12K tokens, fast to process


def _refresh_connection():
    db.session.remove()
    if db.engine.url.drivername == "postgresql":
        db.engine.dispose()


def generate_summary(material_id):
    material = db.session.get(StudyMaterial, material_id)
    if material is None or not material.extracted_text:
        raise ValueError(
            "This material has no extracted text yet. Text extraction "
            "must complete before a summary can be generated."
        )

    summary = material.summary
    if summary is None:
        summary = Summary(material_id=material.id, status="processing")
        db.session.add(summary)
    else:
        summary.status = "processing"
    db.session.commit()

    summary_id = summary.id

    # Truncate long texts to avoid Gemini timeouts
    text = material.extracted_text
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH] + "\n\n[Content truncated for processing]"
    prompt = build_summary_prompt(text)

    try:
        content = generate_content(prompt)

    except Exception as e:
        _refresh_connection()
        summary = db.session.get(Summary, summary_id)
        summary.status = "failed"
        db.session.commit()
        raise RuntimeError(f"Summary generation failed: {e}") from e

    _refresh_connection()
    summary = db.session.get(Summary, summary_id)
    summary.content = content
    summary.status = "ready"
    db.session.commit()
    return summary