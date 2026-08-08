from flask import Blueprint, render_template
from flask_login import login_required

from app.extensions import db
from app.models import User, Subject, StudyMaterial, QuizAttempt
from app.utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/", methods=["GET"])
@login_required
@admin_required
def dashboard():
    # Aggregate COUNT/SUM queries — never load full result sets into
    # Python just to count/sum them; that's real, avoidable DB load.
    stats = {
        "total_users": db.session.query(db.func.count(User.id)).scalar(),
        "total_subjects": db.session.query(db.func.count(Subject.id)).scalar(),
        "total_materials": db.session.query(db.func.count(StudyMaterial.id)).scalar(),
        "total_quiz_attempts": db.session.query(db.func.count(QuizAttempt.id)).scalar(),
        "storage_bytes": db.session.query(db.func.sum(StudyMaterial.file_size)).scalar() or 0,
    }
    stats["storage_mb"] = round(stats["storage_bytes"] / (1024 * 1024), 1)

    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.route("/users", methods=["GET"])
@login_required
@admin_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)


@admin_bp.route("/users/<int:user_id>/suspend", methods=["POST"])
@login_required
@admin_required
def suspend_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    return {"success": True}


@admin_bp.route("/users/<int:user_id>/reactivate", methods=["POST"])
@login_required
@admin_required
def reactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    return {"success": True}