from functools import wraps

from flask import abort
from flask_login import current_user


def admin_required(f):
    """Stacks with @login_required — checks admin status AFTER auth
    is already confirmed. Never scatter `if not current_user.is_admin`
    checks across route bodies; this is the single, auditable
    gatekeeper for every admin-only endpoint."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function