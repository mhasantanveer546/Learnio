"""Background AI processing for Vercel serverless.
Uses threading for fire-and-forget tasks.
NOT guaranteed to complete if Vercel kills the function early,
but better than blocking the HTTP response for 30 seconds."""

import threading
from flask import current_app
from app.extensions import db


def _run_in_context(app, func, *args, **kwargs):
    """Run a function inside the Flask app context so db and logger work."""
    with app.app_context():
        try:
            current_app.logger.info(f"Background task started: {func.__name__}")
            func(*args, **kwargs)
            current_app.logger.info(f"Background task completed: {func.__name__}")
        except Exception as e:
            current_app.logger.exception(f"Background task failed: {e}")


def run_background_task(func, *args, **kwargs):
    """Start func in a background thread with app context.
    Returns immediately — caller must NOT wait for result."""
    # Capture the current app object (not current_app proxy)
    app = current_app._get_current_object()
    thread = threading.Thread(
        target=_run_in_context,
        args=(app, func) + args,
        kwargs=kwargs,
    )
    # Non-daemon: Python waits for non-daemon threads to finish before
    # exiting the process. On Vercel this gives the thread a better
    # chance to complete before the environment is destroyed.
    thread.daemon = False
    thread.start()
    return thread