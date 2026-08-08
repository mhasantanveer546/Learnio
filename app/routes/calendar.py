from datetime import datetime, timezone, timedelta

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user

from app.models import Assignment, Exam

calendar_bp = Blueprint("calendar", __name__, url_prefix="/calendar")

PRIORITY_COLORS = {"low": "#10B981", "medium": "#F59E0B", "high": "#EF4444"}
EXAM_COLOR = "#7C3AED"


@calendar_bp.route("/", methods=["GET"])
@login_required
def view_calendar():
    now = datetime.now(timezone.utc)
    soon = now + timedelta(days=14)

    upcoming_assignments = (
        Assignment.query.filter(
            Assignment.user_id == current_user.id,
            Assignment.status != "completed",
            Assignment.due_date >= now,
            Assignment.due_date <= soon,
        )
        .order_by(Assignment.due_date.asc())
        .all()
    )
    upcoming_exams = (
        Exam.query.filter(Exam.user_id == current_user.id, Exam.exam_date >= now, Exam.exam_date <= soon)
        .order_by(Exam.exam_date.asc())
        .all()
    )

    return render_template(
        "calendar/calendar.html", upcoming_assignments=upcoming_assignments, upcoming_exams=upcoming_exams
    )


@calendar_bp.route("/events", methods=["GET"])
@login_required
def calendar_events():
    """Returns assignments + exams in FullCalendar's expected event
    format. Designed so Phase 11's study sessions can be appended to
    this same list later without any calendar-side changes."""
    events = []

    for a in Assignment.query.filter_by(user_id=current_user.id).all():
        events.append({
            "id": f"assignment-{a.id}",
            "title": f"📝 {a.title}",
            "start": a.due_date.isoformat(),
            "color": PRIORITY_COLORS.get(a.priority, "#2563EB"),
            "extendedProps": {
                "type": "assignment",
                "subject": a.subject.name,
                "priority": a.priority,
                "status": a.status,
                "editUrl": f"/assignments/{a.id}/edit",
            },
        })

    for e in Exam.query.filter_by(user_id=current_user.id).all():
        events.append({
            "id": f"exam-{e.id}",
            "title": f"🎓 {e.title}",
            "start": e.exam_date.isoformat(),
            "color": EXAM_COLOR,
            "extendedProps": {
                "type": "exam",
                "subject": e.subject.name,
                "location": e.location or "",
                "editUrl": f"/exams/{e.id}/edit",
            },
        })

    return jsonify(events)