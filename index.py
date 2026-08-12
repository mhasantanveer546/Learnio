import os

from app import create_app

# Reads FLASK_ENV from .env so the same entry point works for both
# `python app.py` locally and any WSGI server in production.
config_name = os.environ.get("FLASK_ENV", "development")

app = create_app(config_name)


if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False))