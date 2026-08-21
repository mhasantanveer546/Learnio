"""
Authorization tests: prove that User B cannot access User A's resources.

These tests cover the two authorization patterns used in Learnio:

Pattern A — first_or_404 with user_id filter:
  StudyMaterial.query.filter_by(id=id, user_id=current_user.id).first_or_404()
  Result for non-owner: 404 (Not Found)

Pattern B — explicit abort(403) after get_or_404:
  subject = Subject.query.get_or_404(id)
  if subject.user_id != current_user.id: abort(403)
  Result for non-owner: 403 (Forbidden)
"""

from app.extensions import db


# ───────────────────────────────────────────────────────────────
# PATTERN B: Subject routes with explicit abort(403)
# ───────────────────────────────────────────────────────────────

def test_user_cannot_edit_another_users_subject(client, make_user, login_client):
    owner = make_user(email="owner@example.com")
    attacker = make_user(email="attacker@example.com")

    subject = __create_subject(owner, "Biology")

    login_client(attacker)
    response = client.get(f"/subjects/{subject.id}/edit")

    assert response.status_code == 403


def test_user_cannot_delete_another_users_subject(client, make_user, login_client):
    owner = make_user(email="owner@example.com")
    attacker = make_user(email="attacker@example.com")

    subject = __create_subject(owner, "Chemistry")

    login_client(attacker)
    response = client.post(f"/subjects/{subject.id}/delete")

    assert response.status_code == 403


def test_user_cannot_view_another_users_subject(client, make_user, login_client):
    owner = make_user(email="owner@example.com")
    attacker = make_user(email="attacker@example.com")

    subject = __create_subject(owner, "Physics")

    login_client(attacker)
    response = client.get(f"/subjects/{subject.id}")

    assert response.status_code == 403


# ───────────────────────────────────────────────────────────────
# PATTERN A: Material routes with first_or_404(user_id)
# ───────────────────────────────────────────────────────────────

def test_user_cannot_download_another_users_material(client, make_user, make_material, login_client):
    owner = make_user(email="owner@example.com")
    attacker = make_user(email="attacker@example.com")

    material = make_material(owner, status="ready")
    # download requires a storage_key; set a fake one
    material.storage_key = "fake-key"
    db.session.commit()

    login_client(attacker)
    response = client.get(f"/materials/{material.id}/download")

    assert response.status_code == 404


def test_user_cannot_process_another_users_material(client, make_user, make_material, login_client):
    owner = make_user(email="owner@example.com")
    attacker = make_user(email="attacker@example.com")

    material = make_material(owner, status="ready")

    login_client(attacker)
    response = client.post(f"/materials/{material.id}/process")

    assert response.status_code == 404


def test_user_cannot_delete_another_users_material(client, make_user, make_material, login_client):
    owner = make_user(email="owner@example.com")
    attacker = make_user(email="attacker@example.com")

    material = make_material(owner, status="ready")

    login_client(attacker)
    response = client.post(f"/materials/{material.id}/delete")

    assert response.status_code == 404


def test_user_cannot_check_status_of_another_users_material(client, make_user, make_material, login_client):
    owner = make_user(email="owner@example.com")
    attacker = make_user(email="attacker@example.com")

    material = make_material(owner, status="ready")

    login_client(attacker)
    response = client.get(f"/materials/{material.id}/status")

    assert response.status_code == 404


# ───────────────────────────────────────────────────────────────
# PATTERN A: Quiz routes with first_or_404(user_id)
# ───────────────────────────────────────────────────────────────

def test_user_cannot_configure_quiz_for_another_users_material(client, make_user, make_material, login_client):
    owner = make_user(email="owner@example.com")
    attacker = make_user(email="attacker@example.com")

    material = make_material(owner, status="ready")
    material.extracted_text = "Sample text for quiz generation."
    db.session.commit()

    login_client(attacker)
    response = client.get(f"/quizzes/{material.id}/configure")

    assert response.status_code == 404


# ───────────────────────────────────────────────────────────────
# PATTERN A: Flashcard routes with first_or_404(user_id)
# ───────────────────────────────────────────────────────────────

def test_user_cannot_study_flashcards_of_another_users_material(client, make_user, make_material, login_client):
    owner = make_user(email="owner@example.com")
    attacker = make_user(email="attacker@example.com")

    material = make_material(owner, status="ready")

    login_client(attacker)
    response = client.get(f"/flashcards/{material.id}")

    assert response.status_code == 404


# ───────────────────────────────────────────────────────────────
# PATTERN A: Summary routes with first_or_404(user_id)
# ───────────────────────────────────────────────────────────────

def test_user_cannot_view_summary_of_another_users_material(client, make_user, make_material, login_client):
    owner = make_user(email="owner@example.com")
    attacker = make_user(email="attacker@example.com")

    material = make_material(owner, status="ready")

    login_client(attacker)
    response = client.get(f"/summaries/{material.id}")

    assert response.status_code == 404


# ───────────────────────────────────────────────────────────────
# Helper: inline subject creation (avoids importing from routes)
# ───────────────────────────────────────────────────────────────

def __create_subject(user, name):
    from app.models import Subject
    subject = Subject(user_id=user.id, name=name)
    db.session.add(subject)
    db.session.commit()
    return subject