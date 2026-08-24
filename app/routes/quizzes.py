from datetime import datetime, timezone
from urllib.parse import urlparse
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from flask_login import login_required, current_user

from app.extensions import db, limiter
from app.models import StudyMaterial, Quiz, QuizAttempt, QuizAnswer
from app.services.quiz_service import generate_quiz, start_attempt, submit_attempt, self_grade_answer
from app.services.background_ai import run_background_task


def _elapsed_seconds(created_at):
    """Safely compute elapsed time since created_at, handling both
    timezone-aware and naive datetimes from the database."""
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return (now - created_at).total_seconds()


quizzes_bp = Blueprint("quizzes", __name__, url_prefix="/quizzes")


@quizzes_bp.route("/<int:material_id>/configure")
@login_required
def configure_quiz(material_id):
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    if not material.extracted_text:
        flash("This material has no extracted text yet.", "warning")
        return redirect(url_for("subjects.view_subject", subject_id=material.subject_id))

    quiz = Quiz.query.filter_by(material_id=material_id).first()
    return render_template("quizzes/configure.html", material=material, quiz=quiz)


@quizzes_bp.route("/<int:material_id>/generate", methods=["POST"])
@limiter.limit("3 per minute")
@login_required
def generate_quiz_route(material_id):
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    if not material.extracted_text:
        flash("This material has no extracted text yet.", "warning")
        return redirect(url_for("quizzes.configure_quiz", material_id=material_id))

    existing = Quiz.query.filter_by(material_id=material_id).first()

    if existing:
        if existing.status == "ready":
            flash("A quiz already exists for this material.", "info")
            return redirect(url_for("quizzes.take_quiz", quiz_id=existing.id))

        if existing.status == "processing":
            elapsed = _elapsed_seconds(existing.created_at)
            if elapsed < 30:
                flash("Quiz generation is already in progress. Please wait.", "info")
                return redirect(url_for("quizzes.configure_quiz", material_id=material_id))

        db.session.delete(existing)
        db.session.commit()

    quiz = Quiz(
        material_id=material_id,
        title=f"Quiz — {material.original_name}",
        status="processing",
    )
    db.session.add(quiz)
    db.session.commit()

    num_questions = request.form.get("num_questions", 5, type=int)
    question_types = request.form.getlist("question_types") or ["mcq"]
    difficulty = request.form.get("difficulty", "medium")

    run_background_task(
        generate_quiz,
        quiz_id=quiz.id,
        material_id=material.id,
        num_questions=num_questions,
        question_types=question_types,
        difficulty=difficulty,
    )

    flash("Quiz generation started! This may take a moment.", "info")
    return redirect(url_for("quizzes.configure_quiz", material_id=material_id))


@quizzes_bp.route("/<int:quiz_id>/take", methods=["GET"])
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.join(StudyMaterial).filter(
        Quiz.id == quiz_id, StudyMaterial.user_id == current_user.id
    ).first_or_404()

    if quiz.status != "ready":
        flash("This quiz isn't ready yet.", "warning")
        return redirect(url_for("subjects.view_subject", subject_id=quiz.material.subject_id))

    attempt = start_attempt(quiz, current_user.id)
    return render_template("quizzes/take.html", quiz=quiz, attempt=attempt)


@quizzes_bp.route("/attempt/<int:attempt_id>/submit", methods=["POST"])
@login_required
def submit_quiz(attempt_id):
    attempt = QuizAttempt.query.filter_by(id=attempt_id, user_id=current_user.id).first_or_404()

    answers = {key: value for key, value in request.form.items() if key.isdigit()}
    submit_attempt(attempt, answers)

    return redirect(url_for("quizzes.review_attempt", attempt_id=attempt.id))


@quizzes_bp.route("/attempt/<int:attempt_id>/review", methods=["GET"])
@login_required
def review_attempt(attempt_id):
    attempt = QuizAttempt.query.filter_by(id=attempt_id, user_id=current_user.id).first_or_404()
    return render_template("quizzes/review.html", attempt=attempt)


@quizzes_bp.route("/answer/<int:answer_id>/self-grade", methods=["POST"])
@login_required
def self_grade_route(answer_id):
    answer = QuizAnswer.query.join(QuizAttempt).filter(
        QuizAnswer.id == answer_id, QuizAttempt.user_id == current_user.id
    ).first_or_404()

    is_correct = request.get_json().get("is_correct")
    attempt = self_grade_answer(answer, is_correct)

    return jsonify({"score": attempt.score, "total": attempt.total})


@quizzes_bp.route("/<int:material_id>/history", methods=["GET"])
@login_required
def quiz_history(material_id):
    material = StudyMaterial.query.filter_by(id=material_id, user_id=current_user.id).first_or_404()

    attempts = (
        QuizAttempt.query.join(Quiz)
        .filter(Quiz.material_id == material.id, QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.started_at.desc())
        .all()
    )

    total = len(attempts)
    if total > 0:
        avg_score = sum(a.score_percentage for a in attempts) / total
        best_score = max(a.score_percentage for a in attempts)
    else:
        avg_score = 0
        best_score = 0

    stats = {
        "total_quizzes": total,
        "average_score": round(avg_score),
        "best_score": round(best_score),
    }

    chronological = list(reversed(attempts))
    chart_data = {
        "labels": [a.started_at.strftime("%b %d") for a in chronological],
        "scores": [a.score_percentage for a in chronological],
    }

    return render_template(
        "quizzes/history.html",
        material=material,
        attempts=attempts,
        stats=stats,
        chart_data=chart_data,
    )


@quizzes_bp.route("/<int:quiz_id>/status")
@login_required
def quiz_status(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.material.user_id != current_user.id:
        abort(403)

    if quiz.status == "processing":
        elapsed = _elapsed_seconds(quiz.created_at)
        if elapsed > 180:
            quiz.status = "failed"
            db.session.commit()

    return jsonify({"status": quiz.status})