from flask import Flask,render_template

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

    @app.errorhandler(404)
    def page_not_found(error):

        return render_template(
            "errors/404.html"
        ),404



    @app.errorhandler(500)
    def server_error(error):

        return render_template(
            "errors/500.html"
        ),500

    return app