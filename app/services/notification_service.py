from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Notification, Assignment, Exam
from app.utils.constants import ASSIGNMENT_REMINDER_DAYS, EXAM_REMINDER_DAYS


def _create_if_missing(user_id, source_type, source_id, message, link):
    """Relies on the DB's unique constraint to prevent duplicates —
    tries the insert, silently ignores it if one already exists for
    this exact (user, source_type, source_id). Avoids a check-then-
    insert race condition."""
    notification = Notification(
        user_id=user_id, source_type=source_type, source_id=source_id,
        message=message, link=link,
    )
    db.session.add(notification)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()  # already exists — that's fine, not an error


def generate_due_notifications(user_id):
    """Called on dashboard load. Checks upcoming assignments/exams
    within their reminder windows and creates notifications for any
    that don't already have one. Safe to call repeatedly — duplicate
    creation is prevented at the database level."""
    now = datetime.now(timezone.utc)

    assignments = Assignment.query.filter(
        Assignment.user_id == user_id, Assignment.status != "completed"
    ).all()
    for a in assignments:
        due = a.due_date.replace(tzinfo=timezone.utc) if a.due_date.tzinfo is None else a.due_date
        days_until = (due - now).total_seconds() / 86400
        if 0 < days_until <= ASSIGNMENT_REMINDER_DAYS:
            _create_if_missing(
                user_id, "assignment", a.id,
                f'"{a.title}" is due in {max(1, round(days_until))} day(s).',
                "/assignments/",
            )

    exams = Exam.query.filter(Exam.user_id == user_id).all()
    for e in exams:
        exam_date = e.exam_date.replace(tzinfo=timezone.utc) if e.exam_date.tzinfo is None else e.exam_date
        days_until = (exam_date - now).total_seconds() / 86400
        if 0 < days_until <= EXAM_REMINDER_DAYS:
            _create_if_missing(
                user_id, "exam", e.id,
                f'"{e.title}" exam is in {max(1, round(days_until))} day(s).',
                "/exams/",
            )