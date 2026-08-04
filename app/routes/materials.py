import os

from flask import Blueprint, current_app, flash, redirect, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.extensions import db
from app.forms.materials import UploadMaterialForm
from app.models import Subject, StudyMaterial
from app.services.upload_service import save_study_material

materials_bp = Blueprint("materials", __name__, url_prefix="/materials")


@materials_bp.route("/upload", methods=["POST"])
@login_required
def upload_material():
    form = UploadMaterialForm()

    # Must populate choices BEFORE validate_on_submit() — SelectField
    # validates the submitted value against .choices, which defaults to
    # empty. Without this line, every upload fails validation no matter
    # what the user picks.
    form.subject_id.choices = [
        (s.id, s.name) for s in Subject.query.filter_by(user_id=current_user.id).all()
    ]

    if not form.validate_on_submit():
        flash("Please correct the errors in the upload form.", "danger")
        return redirect(request.referrer or url_for("dashboard.dashboard"))

    # Ownership check — prevents a tampered subject_id in the POST body
    # from attaching a file to another user's subject.
    subject = Subject.query.filter_by(
        id=form.subject_id.data, user_id=current_user.id
    ).first_or_404()

    try:
        saved_file = save_study_material(
            form.file.data, current_user.id, current_app.config["UPLOAD_FOLDER"]
        )
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("subjects.view_subject", subject_id=subject.id))

    material = StudyMaterial(
        filename=saved_file["filename"],
        original_name=secure_filename(form.file.data.filename),
        file_type=saved_file["file_type"],
        file_size=saved_file["file_size"],
        subject_id=subject.id,
        user_id=current_user.id,
    )
    db.session.add(material)
    db.session.commit()

    flash("Study material uploaded successfully.", "success")
    return redirect(url_for("subjects.view_subject", subject_id=subject.id))


@materials_bp.route("/<int:material_id>/delete", methods=["POST"])
@login_required
def delete_material(material_id):
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    filepath = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        "users",
        f"user_{material.user_id}",
        "notes",
        material.filename,
    )
    if os.path.exists(filepath):
        os.remove(filepath)

    subject_id = material.subject_id
    db.session.delete(material)
    db.session.commit()

    flash("Study material deleted successfully.", "success")
    return redirect(url_for("subjects.view_subject", subject_id=subject_id))