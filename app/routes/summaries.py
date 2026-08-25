from datetime import datetime, timezone
from time import time
from flask import Blueprint, render_template, jsonify, abort, current_app, flash, redirect, url_for, make_response
from flask_login import login_required, current_user
from app.extensions import limiter, db
from app.models import StudyMaterial, Summary
from app.services.summary_service import generate_summary


def _elapsed_seconds(created_at):
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return (now - created_at).total_seconds()


summaries_bp = Blueprint("summaries", __name__, url_prefix="/summaries")


@summaries_bp.route("/<int:material_id>/generate", methods=["POST"])
@limiter.limit("3 per minute")
@login_required
def generate_summary_route(material_id):
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    if not material.extracted_text:
        return jsonify({"status": "failed", "error": "No extracted text yet"}), 400

    existing = Summary.query.filter_by(material_id=material_id).first()

    if existing:
        if existing.status == "ready":
            return jsonify({"status": "ready"})

        if existing.status == "processing":
            elapsed = _elapsed_seconds(existing.created_at)
            if elapsed < 30:
                return jsonify({"status": "processing"})

        db.session.delete(existing)
        db.session.commit()

    summary = Summary(material_id=material_id, status="processing")
    db.session.add(summary)
    db.session.commit()

    try:
        generate_summary(material_id=material.id)
        db.session.refresh(summary)
        return jsonify({"status": summary.status})
    except Exception as e:
        current_app.logger.exception(f"Summary generation failed: {e}")
        db.session.refresh(summary)
        return jsonify({"status": "failed", "error": str(e)}), 500


@summaries_bp.route("/<int:material_id>/status")
@login_required
def summary_status(material_id):
    summary = Summary.query.filter_by(material_id=material_id).first_or_404()
    if summary.material.user_id != current_user.id:
        abort(403)

    if summary.status == "processing":
        elapsed = _elapsed_seconds(summary.created_at)
        if elapsed > 180:
            summary.status = "failed"
            db.session.commit()

    resp = jsonify({"status": summary.status})
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@summaries_bp.route("/<int:material_id>", methods=["GET"])
@login_required
def view_summary(material_id):
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    resp = make_response(render_template(
        "materials/summary.html", material=material, summary=material.summary
    ))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp