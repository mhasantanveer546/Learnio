from app.models.user import User


def test_register_creates_user(client):
    response = client.post("/auth/register", data={
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123",
        "confirm_password": "password123",
    })

    # 302 = redirect to login, which is what a successful register does
    assert response.status_code == 302
    assert response.location == "/auth/login" or "/auth/login" in response.location

    user = User.query.filter_by(email="newuser@example.com").first()
    assert user is not None
    assert user.username == "newuser"
    # never store/compare plaintext passwords
    assert user.check_password("password123")


def test_login_success(client, make_user):
    make_user(email="login@example.com", password="password123")

    response = client.post("/auth/login", data={
        "email": "login@example.com",
        "password": "password123",
    })

    assert response.status_code == 302  # redirected to dashboard


def test_login_wrong_password(client, make_user):
    make_user(email="wrongpw@example.com", password="password123")

    response = client.post("/auth/login", data={
        "email": "wrongpw@example.com",
        "password": "totally-wrong",
    })

    assert response.status_code == 200  # re-rendered, no redirect
    assert b"Invalid email or password." in response.data


def test_login_suspended_user(client, make_user):
    make_user(email="suspended@example.com", password="password123", is_active=False)

    response = client.post("/auth/login", data={
        "email": "suspended@example.com",
        "password": "password123",
    })

    assert response.status_code == 200
    assert b"suspended" in response.data


def test_logout(client, make_user):
    make_user(email="logout@example.com", password="password123")

    # log in first so there's an active session to log out of
    client.post("/auth/login", data={
        "email": "logout@example.com",
        "password": "password123",
    })

    response = client.get("/auth/logout")

    assert response.status_code == 302
    assert "/auth/login" in response.location