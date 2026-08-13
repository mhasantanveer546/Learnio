import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models import User


@click.command("create-admin")
@click.argument("email")
@with_appcontext
def create_admin(email):
    """Promotes an existing user to admin by email.
    Usage: flask create-admin user@example.com
    """
    user = User.query.filter_by(email=email).first()

    if not user:
        click.echo(f"No user found with email '{email}'.")
        return

    if user.is_admin:
        click.echo(f"'{email}' is already an admin.")
        return

    user.is_admin = True
    db.session.commit()
    click.echo(f"'{email}' is now an admin.")


import random
from datetime import datetime, timedelta, timezone

from app.models import Subject, Assignment, StudySession, StudyMaterial


@click.command("seed-demo")
@click.argument("email")
@with_appcontext
def seed_demo(email):
    """Populates dummy Subjects, Assignments, StudySessions, and
    StudyMaterial rows for an existing user, so dashboards/lists have
    something to show while testing.
    Usage: flask seed-demo user@example.com
    """
    user = User.query.filter_by(email=email).first()
    if not user:
        click.echo(f"No user found with email '{email}'.")
        return

    now = datetime.now(timezone.utc)

    subjects_data = [
        ("Data Structures", "#2563EB", "fa-sitemap"),
        ("Calculus II", "#DC2626", "fa-square-root-alt"),
        ("Digital Logic Design", "#16A34A", "fa-microchip"),
    ]
    subjects = []
    for name, color, icon in subjects_data:
        s = Subject(user_id=user.id, name=name, color=color, icon=icon)
        db.session.add(s)
        subjects.append(s)
    db.session.flush()  # assigns subject.id without a full commit yet

    priorities = ["low", "medium", "high"]
    statuses = ["pending", "in_progress", "completed"]
    for i in range(6):
        subject = random.choice(subjects)
        db.session.add(Assignment(
            subject_id=subject.id,
            user_id=user.id,
            title=f"Assignment {i + 1} - {subject.name}",
            description="Auto-generated dummy assignment for testing.",
            due_date=now + timedelta(days=random.randint(-3, 14)),
            priority=random.choice(priorities),
            status=random.choice(statuses),
        ))

    for i in range(5):
        subject = random.choice(subjects)
        started = now - timedelta(days=random.randint(0, 6), hours=random.randint(0, 5))
        duration = random.randint(25, 120)
        db.session.add(StudySession(
            user_id=user.id,
            subject_id=subject.id,
            started_at=started,
            ended_at=started + timedelta(minutes=duration),
            duration_minutes=duration,
            completed=True,
        ))

    file_types = ["pdf", "docx", "pptx"]
    for i in range(4):
        subject = random.choice(subjects)
        ftype = random.choice(file_types)
        db.session.add(StudyMaterial(
            subject_id=subject.id,
            user_id=user.id,
            original_name=f"{subject.name.replace(' ', '_')}_notes_{i + 1}.{ftype}",
            file_type=ftype,
            file_size=random.randint(50_000, 4_000_000),
            status="ready",
        ))

    db.session.commit()
    click.echo(f"Seeded demo data for '{email}': {len(subjects_data)} subjects, 6 assignments, 5 study sessions, 4 materials.")