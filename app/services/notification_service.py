from datetime import datetime, timezone, timedelta

from app.extensions import db
from app.models import Notification, Assignment, Exam
from app.utils.constants import ASSIGNMENT_REMINDER_DAYS, EXAM_REMINDER_DAYS


def generate_due_notifications(user_id):
    now = datetime.now(timezone.utc)
    now_naive = now.replace(tzinfo=None)  # due_date/exam_date are stored naive-UTC

    assignments = Assignment.query.filter(
        Assignment.user_id == user_id,
        Assignment.status != "completed",
        Assignment.due_date > now_naive,
        Assignment.due_date <= now_naive + timedelta(days=ASSIGNMENT_REMINDER_DAYS),
    ).all()

    exams = Exam.query.filter(
        Exam.user_id == user_id,
        Exam.exam_date > now_naive,
        Exam.exam_date <= now_naive + timedelta(days=EXAM_REMINDER_DAYS),
    ).all()

    if not assignments and not exams:
        return

    existing = set(
        db.session.query(Notification.source_type, Notification.source_id)
        .filter(
            Notification.user_id == user_id,
            Notification.source_type.in_(["assignment", "exam"]),
        )
        .all()
    )

    to_add = []

    for a in assignments:
        if ("assignment", a.id) in existing:
            continue
        due = a.due_date.replace(tzinfo=timezone.utc) if a.due_date.tzinfo is None else a.due_date
        days_until = max(1, round((due - now).total_seconds() / 86400))
        to_add.append(Notification(
            user_id=user_id, source_type="assignment", source_id=a.id,
            message=f'"{a.title}" is due in {days_until} day(s).',
            link="/assignments/",
        ))

    for e in exams:
        if ("exam", e.id) in existing:
            continue
        exam_date = e.exam_date.replace(tzinfo=timezone.utc) if e.exam_date.tzinfo is None else e.exam_date
        days_until = max(1, round((exam_date - now).total_seconds() / 86400))
        to_add.append(Notification(
            user_id=user_id, source_type="exam", source_id=e.id,
            message=f'"{e.title}" exam is in {days_until} day(s).',
            link="/exams/",
        ))

    if not to_add:
        return

    db.session.add_all(to_add)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()