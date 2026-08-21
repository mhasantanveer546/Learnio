import re
from app import create_app
from app.extensions import db
from app.models.user import User


def test_login_without_csrf_token_is_rejected():
    """A POST without a CSRF token must be rejected with 400."""
    app = create_app("testing")
    app.config["WTF_CSRF_ENABLED"] = True

    with app.app_context():
        db.create_all()
        client = app.test_client()

        user = User(username="csrfuser", email="csrf@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        response = client.post("/auth/login", data={
            "email": "csrf@example.com",
            "password": "password123",
            # NO csrf_token field
        })

        assert response.status_code == 400
        db.drop_all()


def test_login_with_invalid_csrf_token_is_rejected():
    """A POST with a fake CSRF token must be rejected with 400."""
    app = create_app("testing")
    app.config["WTF_CSRF_ENABLED"] = True

    with app.app_context():
        db.create_all()
        client = app.test_client()

        user = User(username="csrfuser", email="csrf@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        response = client.post("/auth/login", data={
            "email": "csrf@example.com",
            "password": "password123",
            "csrf_token": "this-is-fake",
        })

        assert response.status_code == 400
        db.drop_all()


def test_login_with_valid_csrf_token_succeeds():
    """A POST with a real CSRF token extracted from the form succeeds."""
    app = create_app("testing")
    app.config["WTF_CSRF_ENABLED"] = True

    with app.app_context():
        db.create_all()
        client = app.test_client()

        user = User(username="csrfuser", email="csrf@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        # Step 1: GET the login page to extract the real token
        login_page = client.get("/auth/login")
        assert login_page.status_code == 200

        html = login_page.data.decode("utf-8")
        match = re.search(r'name="csrf_token"[^>]+value="([^"]+)"', html)
        assert match is not None, "CSRF token not found in login form HTML"
        csrf_token = match.group(1)

        # Step 2: POST with the valid token
        response = client.post("/auth/login", data={
            "email": "csrf@example.com",
            "password": "password123",
            "csrf_token": csrf_token,
        })

        assert response.status_code == 302  # Redirected to dashboard
        db.drop_all()