from flask import Flask

from app.config import config

from app.extensions import (
    db,
    migrate,
    login_manager,
    csrf
)


def create_app(config_name="development"):

    app = Flask(__name__)

    app.config.from_object(
        config[config_name]
    )


    # initialize extensions

    db.init_app(app)

    migrate.init_app(
        app,
        db
    )

    login_manager.init_app(app)

    csrf.init_app(app)



    # register blueprints

    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(
        dashboard_bp
    )


    return app