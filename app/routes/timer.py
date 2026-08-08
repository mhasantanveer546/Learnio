from datetime import datetime, timezone

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Subject, StudySession
from app.utils.constants import POMODORO_FOCUS_MINUTES, POMODORO_BREAK_MINUTES

timer_bp = Blueprint("timer", __name__, url_prefix="/timer")


@timer_bp.route("/", methods=["GET"])
@login_required
def view_timer():
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    return render_template(
        "timer/pomodoro.html",
        subjects=subjects,
        focus_minutes=POMODORO_FOCUS_MINUTES,
        break_minutes=POMODORO_BREAK_MINUTES,
    )


@timer_bp.route("/start", methods=["POST"])
@login_required
def start_session():
    data = request.get_json(silent=True) or {}
    subject_id = data.get("subject_id")

    # Defensive ownership check — never trust a client-supplied subject_id
    # without confirming it actually belongs to the logged-in user.
    if subject_id:
        subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first()
        if not subject:
            subject_id = None

    session = StudySession(
        user_id=current_user.id,
        subject_id=subject_id,
        started_at=datetime.now(timezone.utc),
    )
    db.session.add(session)
    db.session.commit()

    return jsonify({"session_id": session.id})


@timer_bp.route("/<int:session_id>/stop", methods=["POST"])
@login_required
def stop_session(session_id):
    session = StudySession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()

    if session.ended_at:
        return jsonify({"error": "Session already ended."}), 400

    data = request.get_json(silent=True) or {}
    ran_full_duration = bool(data.get("completed"))

    now = datetime.now(timezone.utc).replace(tzinfo=None)  # match SQLite's naive storage
    session.ended_at = now

    if ran_full_duration:
        session.duration_minutes = POMODORO_FOCUS_MINUTES
        session.completed = True
    else:
        elapsed = (now - session.started_at).total_seconds() / 60
        session.duration_minutes = max(1, round(elapsed))
        session.completed = False

    db.session.commit()

    return jsonify({"duration_minutes": session.duration_minutes, "completed": session.completed})