"""Background AI processing for Vercel serverless.
Uses threading for fire-and-forget tasks."""

import threading
from flask import current_app
from app.extensions import db


def _run_in_context(app, func, *args, **kwargs):
    """Run a function inside the Flask app context so db and logger work."""
    with app.app_context():
        # Discard potentially stale session before starting work.
        # Only dispose the engine on PostgreSQL — SQLite in-memory
        # databases would be destroyed by dispose().
        db.session.remove()
        if db.engine.url.drivername == "postgresql":
            db.engine.dispose()
        try:
            current_app.logger.info(f"Background task started: {func.__name__}")
            func(*args, **kwargs)
            current_app.logger.info(f"Background task completed: {func.__name__}")
        except Exception as e:
            current_app.logger.exception(f"Background task failed: {e}")


def run_background_task(func, *args, **kwargs):
    """Start func in a background thread with app context."""
    app = current_app._get_current_object()
    thread = threading.Thread(
        target=_run_in_context,
        args=(app, func) + args,
        kwargs=kwargs,
    )
    thread.daemon = False
    thread.start()
    return thread