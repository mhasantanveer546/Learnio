from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timezone

from app.extensions import db
from app.forms.auth import LoginForm, RegisterForm
from app.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # If someone who's already logged in wanders back to /register,
    # send them to the dashboard instead of letting them create a
    # second account mid-session.
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    form = RegisterForm()

    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    # GET request, or POST that failed validation — re-render the SAME
    # form object so field-level errors (username taken, weak password,
    # mismatched confirm) actually show up next to the offending field.
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("Your Learnio account has been suspended. Please contact an administrator.", "danger")
                return render_template("auth/login.html", form=form)

            login_user(user, remember=form.remember_me.data)
            user.last_seen_at = datetime.now(timezone.utc)
            db.session.commit()

            next_page = request.args.get("next")
            if not next_page or not next_page.startswith("/"):
                next_page = url_for("dashboard.dashboard")

            flash("Logged in successfully!", "success")
            return redirect(next_page)

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("auth.login"))