from flask import Blueprint, send_file, flash, redirect, url_for, current_app
from flask_login import login_required, current_user

from app.models import StudyMaterial, FlashcardSet, Quiz, QuizAttempt
from app.services.export_service import (
    export_summary_pdf, export_flashcards_csv, export_quiz_history_csv, export_quiz_review_pdf,
)

exports_bp = Blueprint("exports", __name__, url_prefix="/exports")


@exports_bp.route("/summary/<int:material_id>", methods=["GET"])
@login_required
def export_summary(material_id):
    material = StudyMaterial.query.filter_by(id=material_id, user_id=current_user.id).first_or_404()

    if not material.summary or material.summary.status != "ready":
        flash("No summary available to export yet.", "warning")
        return redirect(url_for("subjects.view_subject", subject_id=material.subject_id))

    try:
        buffer = export_summary_pdf(material, material.summary)
    except Exception as e:
        current_app.logger.error(f"Summary PDF export failed for material {material_id}: {e}")
        flash("Unable to generate export. Please try again.", "danger")
        return redirect(url_for("summaries.view_summary", material_id=material_id))

    filename = f"{material.original_name.rsplit('.', 1)[0]}_summary.pdf"
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=filename)


@exports_bp.route("/flashcards/<int:material_id>", methods=["GET"])
@login_required
def export_flashcards(material_id):
    material = StudyMaterial.query.filter_by(id=material_id, user_id=current_user.id).first_or_404()

    if not material.flashcard_set or material.flashcard_set.status != "ready":
        flash("No flashcards available to export yet.", "warning")
        return redirect(url_for("subjects.view_subject", subject_id=material.subject_id))

    try:
        buffer = export_flashcards_csv(material.flashcard_set)
    except Exception as e:
        current_app.logger.error(f"Flashcard CSV export failed for material {material_id}: {e}")
        flash("Unable to generate export. Please try again.", "danger")
        return redirect(url_for("subjects.view_subject", subject_id=material.subject_id))

    filename = f"{material.original_name.rsplit('.', 1)[0]}_flashcards.csv"
    return send_file(buffer, mimetype="text/csv", as_attachment=True, download_name=filename)


@exports_bp.route("/quiz-history/<int:material_id>", methods=["GET"])
@login_required
def export_quiz_history(material_id):
    material = StudyMaterial.query.filter_by(id=material_id, user_id=current_user.id).first_or_404()

    attempts = (
        QuizAttempt.query.join(Quiz)
        .filter(Quiz.material_id == material.id, QuizAttempt.user_id == current_user.id, QuizAttempt.completed_at.isnot(None))
        .order_by(QuizAttempt.started_at.desc())
        .all()
    )

    try:
        buffer = export_quiz_history_csv(material, attempts)
    except Exception as e:
        current_app.logger.error(f"Quiz history CSV export failed for material {material_id}: {e}")
        flash("Unable to generate export. Please try again.", "danger")
        return redirect(url_for("quizzes.quiz_history", material_id=material_id))

    filename = f"{material.original_name.rsplit('.', 1)[0]}_quiz_history.csv"
    return send_file(buffer, mimetype="text/csv", as_attachment=True, download_name=filename)


@exports_bp.route("/quiz-review/<int:attempt_id>", methods=["GET"])
@login_required
def export_quiz_review(attempt_id):
    attempt = QuizAttempt.query.filter_by(id=attempt_id, user_id=current_user.id).first_or_404()

    try:
        buffer = export_quiz_review_pdf(attempt)
    except Exception as e:
        current_app.logger.error(f"Quiz review PDF export failed for attempt {attempt_id}: {e}")
        flash("Unable to generate export. Please try again.", "danger")
        return redirect(url_for("quizzes.review_attempt", attempt_id=attempt_id))

    filename = f"quiz_review_{attempt_id}.pdf"
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=filename)