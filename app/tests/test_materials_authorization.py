from app.models import StudyMaterial
from app.extensions import db

def login(client, email, password):
    return client.post("/auth/login", data={"email": email, "password": password})


def test_user_cannot_view_status_of_other_users_material(client, make_user, make_material):
    owner = make_user()
    attacker = make_user()
    material = make_material(owner)

    login(client, attacker.email, "password123")

    response = client.get(f"/materials/{material.id}/status")
    assert response.status_code == 404

def test_user_cannot_delete_other_users_material(client, make_user, make_material):
    owner = make_user(username="owner2", email="owner2@example.com", password="password123")
    attacker = make_user(username="attacker2", email="attacker2@example.com", password="password123")
    material = make_material(owner)
    material_id = material.id

    login(client, "attacker2@example.com", "password123")

    response = client.post(f"/materials/{material_id}/delete")
    assert response.status_code == 404

    still_exists = db.session.get(StudyMaterial, material_id)
    assert still_exists is not None


def test_user_cannot_download_other_users_material(client, make_user, make_material):
    owner = make_user(username="owner3", email="owner3@example.com", password="password123")
    attacker = make_user(username="attacker3", email="attacker3@example.com", password="password123")
    material = make_material(owner)

    login(client, "attacker3@example.com", "password123")

    response = client.get(f"/materials/{material.id}/download")
    assert response.status_code == 404


def test_owner_can_view_own_material_status(client, make_user, make_material):
    owner = make_user(username="owner4", email="owner4@example.com", password="password123")
    material = make_material(owner)

    login(client, "owner4@example.com", "password123")

    response = client.get(f"/materials/{material.id}/status")
    assert response.status_code == 200