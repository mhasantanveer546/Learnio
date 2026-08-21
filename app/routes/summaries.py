from flask import Blueprint, render_template, jsonify, abort, current_app
from flask_login import login_required, current_user
from app.extensions import limiter
from app.models import StudyMaterial
from app.services.summary_service import generate_summary

summaries_bp = Blueprint("summaries", __name__, url_prefix="/summaries")


@summaries_bp.route("/<int:material_id>/generate", methods=["POST"])
@limiter.limit("3 per minute")
@login_required
def generate_summary_route(material_id):
    """Triggers summary generation. Called via fetch() from the subject
    detail page — returns JSON, never redirects, same async pattern as
    process_material in Phase 3."""
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    if material.status != "ready":
        return jsonify({
            "error": "This material's text hasn't finished processing yet."
        }), 400

    try:
        summary = generate_summary(material)
        return jsonify({"status": summary.status})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        current_app.logger.warning(f"Summary generation failed for material {material_id}: {e}")
        return jsonify({"status": "failed"}), 500


@summaries_bp.route("/<int:material_id>/status", methods=["GET"])
@login_required
def summary_status(material_id):
    """Polled by the frontend while a summary is 'processing'."""
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    if not material.summary:
        return jsonify({"status": "pending"})

    return jsonify({"status": material.summary.status})


@summaries_bp.route("/<int:material_id>", methods=["GET"])
@login_required
def view_summary(material_id):
    """Renders the summary page — only reachable once generation has
    actually completed."""
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    if not material.summary or material.summary.status != "ready":
        abort(404)

    return render_template("materials/summary.html", material=material, summary=material.summary)