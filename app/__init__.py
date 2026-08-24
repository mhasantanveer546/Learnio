import os
import json
from datetime import datetime, timezone
from flask import Flask, render_template, flash, redirect, url_for, request
from flask_login import current_user
from werkzeug.exceptions import RequestEntityTooLarge
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from app.config import config
from app.extensions import db, migrate, login_manager, csrf, limiter
from app.routes.dashboard import dashboard_bp
from app.routes.auth import auth_bp
from app.routes.profile import profile_bp
from app.routes.subjects import subjects_bp
from app.routes.materials import materials_bp
from app.routes.summaries import summaries_bp
from app.routes.chat import chat_bp
from app.routes.quizzes import quizzes_bp
from app.routes.flashcards import flashcards_bp
from app.routes.assignments import assignments_bp
from app.routes.exams import exams_bp
from app.routes.calendar import calendar_bp
from app.routes.search import search_bp
from app.routes.timer import timer_bp
from app.routes.analytics import analytics_bp
from app.routes.notifications import notifications_bp
from app.routes.exports import exports_bp
from app.routes.admin import admin_bp
from app.cli import create_admin, seed_demo
from datetime import datetime as dt
from app.routes.main import main_bp

def create_app(config_name="development"):
    # Initialize Sentry BEFORE the app is created so it can catch
    # startup errors too.
    if config_name == "production":
        sentry_dsn = os.environ.get("SENTRY_DSN")
        if sentry_dsn:
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[FlaskIntegration()],
                traces_sample_rate=0.1,  # 10% of requests for performance tracing
                profiles_sample_rate=0.1,
            )

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    if config_name == "production":
        if not app.config.get("SECRET_KEY"):
            raise RuntimeError("SECRET_KEY environment variable must be set in production")
        if not app.config.get("SQLALCHEMY_DATABASE_URI"):
            raise RuntimeError("DATABASE_URL environment variable must be set in production")

    try:
        os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)
    except OSError:
        pass  # Read-only filesystem (e.g. Vercel) — instance/ is only needed for local SQLite dev
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

       
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(materials_bp)
    app.register_blueprint(summaries_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(quizzes_bp)
    app.register_blueprint(flashcards_bp)
    app.register_blueprint(assignments_bp)
    app.register_blueprint(exams_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(timer_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(exports_bp)
    app.register_blueprint(admin_bp) 
    app.cli.add_command(create_admin)
    app.cli.add_command(seed_demo)

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500

    @app.errorhandler(RequestEntityTooLarge)
    def file_too_large(error):
        flash("That file is too large. Maximum upload size is 50MB.", "danger")
        return redirect(request.referrer or url_for("dashboard.dashboard"))

    @app.template_filter("from_json")
    def from_json_filter(value):
        return json.loads(value) if value else []

    @app.before_request
    def update_last_seen():
        if current_user.is_authenticated:
            now = datetime.now(timezone.utc)
            last_seen = current_user.last_seen_at
            if last_seen is not None and last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            if last_seen is None or (now - last_seen).total_seconds() > 300:
                current_user.last_seen_at = now
                db.session.commit()

    @app.context_processor
    def inject_now():
        return {"current_year": dt.now().year}
        
    @app.after_request
    def add_security_headers(response):
        """Inject security headers on every response. These are
        defense-in-depth measures that reduce the attack surface
        for common web vulnerabilities."""
        # Prevent clickjacking: never allow this site to be embedded
        # in an iframe, frame, or object on another domain.
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME sniffing: browser must respect the Content-Type
        # header sent by the server, not guess the file type.
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Limit referrer leakage: when navigating to a different origin,
        # only send the origin (https://learnio.com), not the full path
        # or query string. Same-origin requests still send full referrer.
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Basic Content Security Policy: only allow scripts/styles from
        # same origin, cdnjs (Font Awesome), and fonts.gstatic.com.
        # 'unsafe-inline' is needed for the inline <script> in base.html
        # (POMODORO constants). Removing it requires externalizing those
        # scripts — a future improvement.
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp

        return response
    return app