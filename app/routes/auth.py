from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timezone
from werkzeug.urls import url_parse

from app.extensions import db, limiter
from app.forms.auth import LoginForm, RegisterForm
from app.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    form = RegisterForm()

    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        current_app.logger.info(f"New user registered: {user.email} (id={user.id})")
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                current_app.logger.warning(f"Suspended user login attempt: {form.email.data}")
                flash("Your Learnio account has been suspended. Please contact an administrator.", "danger")
                return render_template("auth/login.html", form=form)

            login_user(user, remember=False)
            user.last_seen_at = datetime.now(timezone.utc)
            db.session.commit()

            current_app.logger.info(f"User logged in: {user.email} (id={user.id})")

            # SECURE: Only redirect to URLs on our own domain.
            # url_parse().netloc is empty for relative URLs like /dashboard
            # but contains 'evil.com' for absolute URLs like //evil.com.
            next_page = request.args.get("next")
            if not next_page or url_parse(next_page).netloc != "":
                next_page = url_for("dashboard.dashboard")

            flash("Logged in successfully!", "success")
            return redirect(next_page)

        current_app.logger.warning(f"Failed login attempt for email: {form.email.data}")
        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("auth.login"))