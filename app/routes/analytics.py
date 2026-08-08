from datetime import datetime, timezone, timedelta

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import StudySession, QuizAttempt, Quiz, StudyMaterial, Subject

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@analytics_bp.route("/", methods=["GET"])
@login_required
def view_analytics():
    return render_template("analytics/dashboard.html")


@analytics_bp.route("/data/study-hours", methods=["GET"])
@login_required
def study_hours_data():
    """Study minutes per day, last 14 days — split into subject-scoped
    vs general (unscoped) study time, per the design decision to keep
    that distinction visible rather than merging it into one number."""
    since = datetime.now(timezone.utc) - timedelta(days=14)
    sessions = StudySession.query.filter(
        StudySession.user_id == current_user.id,
        StudySession.started_at >= since,
        StudySession.duration_minutes.isnot(None),
    ).all()

    daily = {}
    for s in sessions:
        day = s.started_at.date().isoformat()
        daily.setdefault(day, {"subject": 0, "general": 0})
        if s.subject_id:
            daily[day]["subject"] += s.duration_minutes
        else:
            daily[day]["general"] += s.duration_minutes

    labels = sorted(daily.keys())
    return jsonify({
        "labels": labels,
        "subject_minutes": [daily[d]["subject"] for d in labels],
        "general_minutes": [daily[d]["general"] for d in labels],
    })


@analytics_bp.route("/data/quiz-scores", methods=["GET"])
@login_required
def quiz_scores_data():
    """Quiz percentage scores over time, most recent 15 attempts."""
    attempts = (
        QuizAttempt.query.join(Quiz)
        .join(StudyMaterial, Quiz.material_id == StudyMaterial.id)
        .filter(StudyMaterial.user_id == current_user.id, QuizAttempt.completed_at.isnot(None))
        .order_by(QuizAttempt.completed_at.asc())
        .limit(15)
        .all()
    )

    return jsonify({
        "labels": [a.completed_at.strftime("%b %d") for a in attempts],
        "scores": [round((a.score / a.total) * 100) if a.total else 0 for a in attempts],
    })


@analytics_bp.route("/data/uploads", methods=["GET"])
@login_required
def uploads_data():
    """Materials uploaded per day, last 14 days."""
    since = datetime.now(timezone.utc) - timedelta(days=14)
    materials = StudyMaterial.query.filter(
        StudyMaterial.user_id == current_user.id, StudyMaterial.created_at >= since
    ).all()

    daily = {}
    for m in materials:
        day = m.created_at.date().isoformat()
        daily[day] = daily.get(day, 0) + 1

    labels = sorted(daily.keys())
    return jsonify({"labels": labels, "counts": [daily[d] for d in labels]})


@analytics_bp.route("/data/subjects", methods=["GET"])
@login_required
def subjects_data():
    """Study minutes per subject — pie/doughnut chart data. Excludes
    general (unscoped) study time, since it has no subject to attribute to."""
    subjects = Subject.query.filter_by(user_id=current_user.id).all()

    labels, minutes, colors = [], [], []
    for s in subjects:
        total = sum(sess.duration_minutes or 0 for sess in s.study_sessions if sess.duration_minutes)
        if total > 0:
            labels.append(s.name)
            minutes.append(total)
            colors.append(s.color)

    return jsonify({"labels": labels, "minutes": minutes, "colors": colors})