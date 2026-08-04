import os
from flask import Flask, render_template, flash, redirect, url_for, request
from werkzeug.exceptions import RequestEntityTooLarge

from app.config import config
from app.extensions import db, migrate, login_manager, csrf
from app.routes.dashboard import dashboard_bp
from app.routes.auth import auth_bp
from app.routes.profile import profile_bp
from app.routes.subjects import subjects_bp
from app.routes.materials import materials_bp


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

    return app