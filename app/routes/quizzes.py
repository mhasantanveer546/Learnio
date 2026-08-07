from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import StudyMaterial, Quiz, QuizAttempt, QuizAnswer
from app.services.quiz_service import generate_quiz, start_attempt, submit_attempt, self_grade_answer

quizzes_bp = Blueprint("quizzes", __name__, url_prefix="/quizzes")


@quizzes_bp.route("/<int:material_id>/configure", methods=["GET"])
@login_required
def configure_quiz(material_id):
    material = StudyMaterial.query.filter_by(id=material_id, user_id=current_user.id).first_or_404()
    return render_template("quizzes/configure.html", material=material)


@quizzes_bp.route("/<int:material_id>/generate", methods=["POST"])
@login_required
def generate_quiz_route(material_id):
    material = StudyMaterial.query.filter_by(id=material_id, user_id=current_user.id).first_or_404()

    num_questions = request.form.get("num_questions", 10, type=int)
    question_types = request.form.getlist("question_types") or ["mcq", "true_false"]
    difficulty = request.form.get("difficulty", "medium")

    try:
        quiz = generate_quiz(material, num_questions, question_types, difficulty)
        flash("Quiz generated successfully!", "success")
        return redirect(url_for("quizzes.take_quiz", quiz_id=quiz.id))
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("subjects.view_subject", subject_id=material.subject_id))
    except RuntimeError as e:
        current_app.logger.warning(f"Quiz generation failed for material {material_id}: {e}")
        flash("Failed to generate quiz. Please try again.", "danger")
        return redirect(url_for("subjects.view_subject", subject_id=material.subject_id))


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