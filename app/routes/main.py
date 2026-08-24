from flask import Blueprint, render_template, redirect, url_for, jsonify, current_app

from flask_login import current_user
from app.extensions import db

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def landing():
    return render_template("landing.html")


@main_bp.route("/health")
def health_check():
    """Lightweight health check for uptime monitors.
    Verifies the app is responding and the database is reachable."""
    try:
        # Lightweight query: just check we can talk to the DB
        db.session.execute(db.text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        current_app.logger.error(f"Health check DB failure: {e}")
        db_status = "error"

    status_code = 200 if db_status == "ok" else 503
    return jsonify({
        "status": "healthy" if db_status == "ok" else "unhealthy",
        "database": db_status,
    }), status_code