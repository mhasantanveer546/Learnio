import os
import json
from flask import Flask, render_template, flash, redirect, url_for, request
from werkzeug.exceptions import RequestEntityTooLarge

from app.config import config
from app.extensions import db, migrate, login_manager, csrf
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


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    if config_name == "production":
        if not app.config.get("SECRET_KEY"):
            raise RuntimeError("SECRET_KEY environment variable must be set in production")
        if not app.config.get("SQLALCHEMY_DATABASE_URI"):
            raise RuntimeError("DATABASE_URL environment variable must be set in production")

    os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
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

    return app