from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Subject, Exam
from app.forms.assignments import ExamForm

exams_bp = Blueprint("exams", __name__, url_prefix="/exams")


@exams_bp.route("/", methods=["GET"])
@login_required
def list_exams():
    exams = Exam.query.filter_by(user_id=current_user.id).order_by(Exam.exam_date.asc()).all()
    return render_template("exams/list.html", exams=exams)


@exams_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_exam():
    form = ExamForm()
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.filter_by(user_id=current_user.id).all()]

    if form.validate_on_submit():
        exam = Exam(
            user_id=current_user.id,
            subject_id=form.subject_id.data,
            title=form.title.data,
            exam_date=form.exam_date.data,
            location=form.location.data,
            notes=form.notes.data,
        )
        db.session.add(exam)
        db.session.commit()
        flash("Exam added successfully.", "success")
        return redirect(url_for("exams.list_exams"))

    return render_template("exams/form.html", form=form, is_edit=False)


@exams_bp.route("/<int:exam_id>/edit", methods=["GET", "POST"])
@login_required
def edit_exam(exam_id):
    exam = Exam.query.filter_by(id=exam_id, user_id=current_user.id).first_or_404()

    form = ExamForm(obj=exam)
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.filter_by(user_id=current_user.id).all()]
    if request.method == "GET":
        form.subject_id.data = exam.subject_id

    if form.validate_on_submit():
        exam.subject_id = form.subject_id.data
        exam.title = form.title.data
        exam.exam_date = form.exam_date.data
        exam.location = form.location.data
        exam.notes = form.notes.data
        db.session.commit()
        flash("Exam updated successfully.", "success")
        return redirect(url_for("exams.list_exams"))

    return render_template("exams/form.html", form=form, is_edit=True, exam=exam)


@exams_bp.route("/<int:exam_id>/delete", methods=["POST"])
@login_required
def delete_exam(exam_id):
    exam = Exam.query.filter_by(id=exam_id, user_id=current_user.id).first_or_404()
    db.session.delete(exam)
    db.session.commit()
    flash("Exam deleted.", "success")
    return redirect(url_for("exams.list_exams"))