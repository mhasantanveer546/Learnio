from app.models.user import User
from app.extensions import db


def test_conftest_smoke(app, client):
    user = User(username="temp", email="temp@example.com")
    user.set_password("pw123")
    db.session.add(user)
    db.session.commit()
    assert User.query.count() == 1