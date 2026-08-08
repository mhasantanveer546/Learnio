from datetime import datetime, timezone, timedelta

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import Subject, StudyMaterial, Assignment, StudySession

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def dashboard():
    subject_count = Subject.query.filter_by(user_id=current_user.id).count()
    material_count = StudyMaterial.query.filter_by(user_id=current_user.id).count()

    now = datetime.now(timezone.utc)
    upcoming_assignments = (
        Assignment.query.filter(
            Assignment.user_id == current_user.id,
            Assignment.status != "completed",
            Assignment.due_date >= now,
        )
        .order_by(Assignment.due_date.asc())
        .limit(5)
        .all()
    )

    week_ago = now - timedelta(days=7)
    week_sessions = StudySession.query.filter(
        StudySession.user_id == current_user.id,
        StudySession.started_at >= week_ago,
        StudySession.duration_minutes.isnot(None),
    ).all()
    study_minutes_this_week = sum(s.duration_minutes for s in week_sessions)

    recent_materials = (
        StudyMaterial.query.filter_by(user_id=current_user.id)
        .order_by(StudyMaterial.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard/dashboard.html",
        subject_count=subject_count,
        material_count=material_count,
        upcoming_assignments=upcoming_assignments,
        study_hours_this_week=round(study_minutes_this_week / 60, 1),
        recent_materials=recent_materials,
    )