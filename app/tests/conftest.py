import pytest
import uuid
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models import Subject, StudyMaterial


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(app):
    def _make_user(username=None, email=None, password="password123", is_active=True):
        unique = uuid.uuid4().hex[:8]
        if username is None:
            username = f"user_{unique}"
        if email is None:
            email = f"user_{unique}@example.com"

        user = User(username=username, email=email, is_active=is_active)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    return _make_user

@pytest.fixture
def make_material(app):
    """Factory fixture: creates a Subject + StudyMaterial owned by the given user."""
    def _make_material(owner, original_name="notes.pdf", status="ready"):
        subject = Subject(user_id=owner.id, name="Test Subject")
        db.session.add(subject)
        db.session.commit()

        material = StudyMaterial(
            subject_id=subject.id,
            user_id=owner.id,
            original_name=original_name,
            file_type="pdf",
            file_size=1024,
            status=status,
            storage_key=None,  # no real R2 file needed for these tests
        )
        db.session.add(material)
        db.session.commit()
        return material
    return _make_material

@pytest.fixture
def login_client(client):
    """Returns a helper that logs a given user into the test client
    and returns the client for subsequent requests."""
    def _login(user, password="password123"):
        client.post("/auth/login", data={
            "email": user.email,
            "password": password,
        })
        return client
    return _login