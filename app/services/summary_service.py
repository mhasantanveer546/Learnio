from app.extensions import db
from app.models import StudyMaterial, Summary
from app.ai.client import generate_content
from app.ai.prompts import build_summary_prompt


def generate_summary(material_id):
    """Generates summary with DB session refresh after Gemini call."""

    material = db.session.get(StudyMaterial, material_id)
    if material is None or not material.extracted_text:
        raise ValueError(
            "This material has no extracted text yet. Text extraction "
            "must complete before a summary can be generated."
        )

    # Phase 1: Setup
    summary = material.summary
    if summary is None:
        summary = Summary(material_id=material.id, status="processing")
        db.session.add(summary)
    else:
        summary.status = "processing"
    db.session.commit()

    summary_id = summary.id
    extracted_text = material.extracted_text
    prompt = build_summary_prompt(extracted_text)

    # Phase 2: Call Gemini
    try:
        content = generate_content(prompt)

    except Exception as e:
        # Phase 3a: FAILURE
        db.session.remove()
        summary = db.session.get(Summary, summary_id)
        summary.status = "failed"
        db.session.commit()
        raise RuntimeError(f"Summary generation failed: {e}") from e

    # Phase 3b: SUCCESS
    db.session.remove()
    summary = db.session.get(Summary, summary_id)
    summary.content = content
    summary.status = "ready"
    db.session.commit()
    return summary