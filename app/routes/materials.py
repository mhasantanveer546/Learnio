from flask import Blueprint, current_app, flash, redirect, request, url_for, jsonify, render_template, abort
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.extensions import db
from app.forms.materials import UploadMaterialForm
from app.models import Subject, StudyMaterial
from app.services.upload_service import save_study_material
from app.services.text_extraction_service import extract_text
from app.services.chat_service import index_material, remove_material_index
from app.services.storage_service import delete_file, download_to_temp, generate_download_url

import os

materials_bp = Blueprint("materials", __name__, url_prefix="/materials")


@materials_bp.route("/", methods=["GET"])
@login_required
def list_materials():
    query = StudyMaterial.query.filter_by(user_id=current_user.id)

    subject_filter = request.args.get("subject_id", type=int)
    if subject_filter:
        query = query.filter_by(subject_id=subject_filter)

    type_filter = request.args.get("file_type")
    if type_filter:
        query = query.filter_by(file_type=type_filter)

    status_filter = request.args.get("status")
    if status_filter:
        query = query.filter_by(status=status_filter)

    materials = query.order_by(StudyMaterial.created_at.desc()).all()
    subjects = Subject.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "materials/list.html",
        materials=materials,
        subjects=subjects,
        selected_subject=subject_filter,
        selected_type=type_filter,
        selected_status=status_filter,
    )


@materials_bp.route("/upload", methods=["POST"])
@login_required
def upload_material():
    form = UploadMaterialForm()
    form.subject_id.choices = [
        (s.id, s.name) for s in Subject.query.filter_by(user_id=current_user.id).all()
    ]

    if not form.validate_on_submit():
        flash("Please correct the errors in the upload form.", "danger")
        return redirect(request.referrer or url_for("dashboard.dashboard"))

    subject = Subject.query.filter_by(
        id=form.subject_id.data, user_id=current_user.id
    ).first_or_404()

    try:
        saved_file = save_study_material(form.file.data, current_user.id)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("subjects.view_subject", subject_id=subject.id))

    material = StudyMaterial(
        storage_key=saved_file["storage_key"],
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


@materials_bp.route("/<int:material_id>/download", methods=["GET"])
@login_required
def download_material(material_id):
    material = StudyMaterial.query.filter_by(id=material_id, user_id=current_user.id).first_or_404()

    if not material.storage_key:
        abort(404)

    url = generate_download_url(material.storage_key, material.original_name)
    return redirect(url)


@materials_bp.route("/<int:material_id>/process", methods=["POST"])
@login_required
def process_material(material_id):
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    material.status = "processing"
    db.session.commit()

    # Download to a local temp file for processing only — this is
    # scratch space, not permanent storage. Always cleaned up in the
    # finally block, whether extraction succeeds or fails.
    temp_path = download_to_temp(material.storage_key, suffix=f".{material.file_type}")

    try:
        text = extract_text(temp_path, material.file_type)
        material.extracted_text = text
        material.status = "ready"
        db.session.commit()

        try:
            index_material(material)
        except Exception as e:
            current_app.logger.warning(f"Indexing failed for material {material.id}: {e}")

    except ValueError as e:
        material.status = "failed"
        current_app.logger.warning(f"Extraction failed for material {material.id}: {e}")
        db.session.commit()

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return jsonify({"status": material.status})


@materials_bp.route("/<int:material_id>/status", methods=["GET"])
@login_required
def material_status(material_id):
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    return jsonify({"status": material.status})


@materials_bp.route("/<int:material_id>/delete", methods=["POST"])
@login_required
def delete_material(material_id):
    material = StudyMaterial.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()

    if material.storage_key:
        delete_file(material.storage_key)

    subject_id = material.subject_id

    try:
        remove_material_index(material)
    except Exception as e:
        current_app.logger.warning(f"Failed to remove FAISS index for material {material.id}: {e}")

    db.session.delete(material)
    db.session.commit()

    flash("Study material deleted successfully.", "success")
    return redirect(url_for("subjects.view_subject", subject_id=subject_id))