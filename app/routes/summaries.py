from flask import Blueprint, render_template, jsonify, abort, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import limiter, db
from app.models import StudyMaterial, Summary
from app.services.summary_service import generate_summary
from app.services.background_ai import run_background_task

summaries_bp = Blueprint("summaries", __name__, url_prefix="/summaries")


@summaries_bp.route("/<int:material_id>/generate", methods=["POST"])
@limiter.limit("3 per minute")
@login_required
def generate_summary_route(material_id):
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    if not material.extracted_text:
        flash("This material has no extracted text yet.", "warning")
        return redirect(url_for("summaries.view_summary", material_id=material_id))

    existing = Summary.query.filter_by(material_id=material_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()

    summary = Summary(material_id=material_id, status="processing")
    db.session.add(summary)
    db.session.commit()

    run_background_task(generate_summary, material=material)

    flash("Summary generation started!", "info")
    return redirect(url_for("summaries.view_summary", material_id=material_id))


@summaries_bp.route("/<int:material_id>/status")
@login_required
def summary_status(material_id):
    summary = Summary.query.filter_by(material_id=material_id).first_or_404()
    if summary.material.user_id != current_user.id:
        abort(403)
    return jsonify({"status": summary.status})


@summaries_bp.route("/<int:material_id>", methods=["GET"])
@login_required
def view_summary(material_id):
    """Renders the summary page for any status — polling handles processing/failed."""
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    return render_template("materials/summary.html", material=material, summary=material.summary)