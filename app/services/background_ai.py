"""Background AI processing for Vercel serverless.
Uses threading for fire-and-forget tasks.
NOT guaranteed to complete if Vercel kills the function early."""

import threading
from flask import current_app
from app.extensions import db


def _run_in_context(app, func, *args, **kwargs):
    """Run a function inside the Flask app context so db and logger work."""
    with app.app_context():
        # CRITICAL on Vercel: discard the entire connection pool.
        # The session we inherited may hold a connection that Neon
        # closed while Vercel froze the execution context. Removing
        # the session alone is not enough — the stale connection
        # stays in the pool and the next query crashes with
        # 'SSL connection has been closed unexpectedly'.
        db.session.remove()
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