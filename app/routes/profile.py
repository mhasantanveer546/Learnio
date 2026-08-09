from flask import Blueprint, render_template, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.forms.auth import ProfileForm, ChangePasswordForm
from app.services.upload_service import save_profile_picture
from app.services.storage_service import generate_download_url
from app.models import User

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/", methods=["GET", "POST"])
@login_required
def view_profile():
    form = ProfileForm(obj=current_user)  # pre-fills fields from the logged-in user

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data

        if form.profile_picture.data:
            storage_key = save_profile_picture(form.profile_picture.data, current_user.id)
            current_user.profile_picture_key = storage_key

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile.view_profile"))

    return render_template("profile/profile.html", form=form)


@profile_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
            return render_template("profile/change_password.html", form=form)

        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Password updated successfully.", "success")
        return redirect(url_for("profile.view_profile"))

    return render_template("profile/change_password.html", form=form)

@profile_bp.route("/picture/<int:user_id>", methods=["GET"])
@login_required
def serve_profile_picture(user_id):
    user = User.query.get_or_404(user_id)

    if not user.profile_picture_key:
        abort(404)

    url = generate_download_url(user.profile_picture_key, "profile_picture.jpg", expires_in=3600)
    return redirect(url)