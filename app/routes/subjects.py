from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Subject
from app.forms.subjects import SubjectForm

subjects_bp = Blueprint("subjects", __name__, url_prefix="/subjects")


@subjects_bp.route("/", methods=["GET"])
@login_required
def list_subjects():
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    return render_template("subjects/list.html", subjects=subjects)


@subjects_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_subject():
    form = SubjectForm()

    if form.validate_on_submit():
        subject = Subject(
            user_id=current_user.id,
            name=form.name.data,
            color=form.color.data,
            icon=form.icon.data,
        )
        db.session.add(subject)
        db.session.commit()
        flash("Subject created successfully!", "success")
        return redirect(url_for("subjects.list_subjects"))

    # GET request, or POST that failed validation — re-render the same
    # form object so field errors show up (same pattern as auth.py).
    return render_template("subjects/form.html", form=form, is_edit=False)


@subjects_bp.route("/<int:subject_id>/edit", methods=["GET", "POST"])
@login_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)

    # Ownership check — the critical line. Without this, any logged-in
    # user could edit any other user's subject just by changing the ID
    # in the URL (Insecure Direct Object Reference / IDOR).
    if subject.user_id != current_user.id:
        abort(403)

    form = SubjectForm(obj=subject)  # pre-fills the form with existing values on GET

    if form.validate_on_submit():
        # Mutate the EXISTING row — never construct a new Subject() here,
        # or "editing" silently creates a duplicate instead of updating.
        subject.name = form.name.data
        subject.color = form.color.data
        subject.icon = form.icon.data
        db.session.commit()
        flash("Subject updated successfully!", "success")
        return redirect(url_for("subjects.list_subjects"))

    return render_template("subjects/form.html", form=form, is_edit=True)


@subjects_bp.route("/<int:subject_id>/delete", methods=["POST"])
@login_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)

    # Same ownership check as edit — delete is just as dangerous an
    # operation to leave unguarded, arguably more so.
    if subject.user_id != current_user.id:
        abort(403)

    db.session.delete(subject)
    db.session.commit()
    flash("Subject deleted successfully!", "success")
    return redirect(url_for("subjects.list_subjects"))