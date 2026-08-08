import os

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Subject, Assignment
from app.forms.assignments import AssignmentForm
from app.services.upload_service import save_assignment_attachment
from app.utils.file_utils import get_assignment_attachment_filepath

assignments_bp = Blueprint("assignments", __name__, url_prefix="/assignments")


@assignments_bp.route("/", methods=["GET"])
@login_required
def list_assignments():
    query = Assignment.query.filter_by(user_id=current_user.id)

    status_filter = request.args.get("status")
    if status_filter:
        query = query.filter_by(status=status_filter)

    subject_filter = request.args.get("subject_id", type=int)
    if subject_filter:
        query = query.filter_by(subject_id=subject_filter)

    assignments = query.order_by(Assignment.due_date.asc()).all()
    subjects = Subject.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "assignments/list.html", assignments=assignments, subjects=subjects,
        selected_status=status_filter, selected_subject=subject_filter,
    )


@assignments_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_assignment():
    form = AssignmentForm()
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.filter_by(user_id=current_user.id).all()]

    if form.validate_on_submit():
        assignment = Assignment(
            user_id=current_user.id,
            subject_id=form.subject_id.data,
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            priority=form.priority.data,
            status=form.status.data,
        )

        if form.attachment.data:
            try:
                saved = save_assignment_attachment(form.attachment.data, current_user.id, current_app.config["UPLOAD_FOLDER"])
                assignment.attachment_filename = saved["filename"]
                assignment.attachment_original_name = secure_filename(form.attachment.data.filename)
                assignment.attachment_size = saved["file_size"]
            except ValueError as e:
                flash(str(e), "danger")
                return render_template("assignments/form.html", form=form, is_edit=False)

        db.session.add(assignment)
        db.session.commit()
        flash("Assignment created successfully.", "success")
        return redirect(url_for("assignments.list_assignments"))

    return render_template("assignments/form.html", form=form, is_edit=False)


@assignments_bp.route("/<int:assignment_id>/edit", methods=["GET", "POST"])
@login_required
def edit_assignment(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=current_user.id).first_or_404()

    form = AssignmentForm(obj=assignment)
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.filter_by(user_id=current_user.id).all()]

    if request.method == "GET":
        form.subject_id.data = assignment.subject_id  # obj= doesn't reliably set SelectField

    if form.validate_on_submit():
        assignment.subject_id = form.subject_id.data
        assignment.title = form.title.data
        assignment.description = form.description.data
        assignment.due_date = form.due_date.data
        assignment.priority = form.priority.data
        assignment.status = form.status.data

        if form.attachment.data:
            # Replacing an attachment — remove the old file from disk first
            if assignment.attachment_filename:
                old_path = get_assignment_attachment_filepath(
                    current_app.config["UPLOAD_FOLDER"], assignment.user_id, assignment.attachment_filename
                )
                if os.path.exists(old_path):
                    os.remove(old_path)

            try:
                saved = save_assignment_attachment(form.attachment.data, current_user.id, current_app.config["UPLOAD_FOLDER"])
                assignment.attachment_filename = saved["filename"]
                assignment.attachment_original_name = secure_filename(form.attachment.data.filename)
                assignment.attachment_size = saved["file_size"]
            except ValueError as e:
                flash(str(e), "danger")
                return render_template("assignments/form.html", form=form, is_edit=True, assignment=assignment)

        db.session.commit()
        flash("Assignment updated successfully.", "success")
        return redirect(url_for("assignments.list_assignments"))

    return render_template("assignments/form.html", form=form, is_edit=True, assignment=assignment)


@assignments_bp.route("/<int:assignment_id>/delete", methods=["POST"])
@login_required
def delete_assignment(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=current_user.id).first_or_404()

    if assignment.attachment_filename:
        filepath = get_assignment_attachment_filepath(
            current_app.config["UPLOAD_FOLDER"], assignment.user_id, assignment.attachment_filename
        )
        if os.path.exists(filepath):
            os.remove(filepath)

    db.session.delete(assignment)
    db.session.commit()
    flash("Assignment deleted.", "success")
    return redirect(url_for("assignments.list_assignments"))


@assignments_bp.route("/<int:assignment_id>/toggle-status", methods=["POST"])
@login_required
def toggle_status(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=current_user.id).first_or_404()
    assignment.status = "completed" if assignment.status != "completed" else "pending"
    db.session.commit()
    return redirect(request.referrer or url_for("assignments.list_assignments"))


@assignments_bp.route("/<int:assignment_id>/attachment", methods=["GET"])
@login_required
def download_attachment(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=current_user.id).first_or_404()

    if not assignment.attachment_filename:
        abort(404)

    filepath = get_assignment_attachment_filepath(
        current_app.config["UPLOAD_FOLDER"], assignment.user_id, assignment.attachment_filename
    )
    if not os.path.exists(filepath):
        abort(404)

    return send_file(filepath, as_attachment=True, download_name=assignment.attachment_original_name)