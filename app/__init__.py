import os
from flask import Flask, render_template
from app.config import config
from app.extensions import db, migrate, login_manager, csrf
from app.routes.dashboard import dashboard_bp
from app.routes.auth import auth_bp
from app.routes.profile import profile_bp

def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Fail loudly at startup instead of silently running with an
    # insecure key or no database — from_object() only copies class
    # attributes, it never runs __init__, so this check has to live here.
    if config_name == "production":
        if not app.config.get("SECRET_KEY"):
            raise RuntimeError("SECRET_KEY environment variable must be set in production")
        if not app.config.get("SQLALCHEMY_DATABASE_URI"):
            raise RuntimeError("DATABASE_URL environment variable must be set in production")

    # SQLite needs the instance/ folder to physically exist before it
    # can create learnio.db — Flask/SQLAlchemy won't create it for us.
    os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)

    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # register blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500

    return app