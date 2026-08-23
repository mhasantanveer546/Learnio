from app.extensions import db
from app.models import StudyMaterial, Summary
from app.ai.client import generate_content
from app.ai.prompts import build_summary_prompt


def generate_summary(material_id):
    """Generates (or regenerates) a structured summary for a StudyMaterial.
    Re-queries the material in the background thread's fresh session so
    lazy loading works. Reads from material.extracted_text — NEVER from
    a previous summary's content."""

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

    prompt = build_summary_prompt(material.extracted_text)

    try:
        content = generate_content(prompt)
        summary.content = content
        summary.status = "ready"
    except RuntimeError:
        summary.status = "failed"
        db.session.commit()
        raise  # let the route log the real error; service doesn't swallow it silently

    db.session.commit()
    return summary
    