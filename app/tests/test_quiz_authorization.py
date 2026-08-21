from app.extensions import db
from app.models import Quiz


def test_non_owner_cannot_take_quiz(app, client, make_user, make_material):
    owner = make_user()
    attacker = make_user()

    material = make_material(owner)

    quiz = Quiz(
        material_id=material.id,
        title="Owner Quiz",
        difficulty="medium",
        status="ready",
    )

    db.session.add(quiz)
    db.session.commit()

    client.post(
        "/auth/login",
        data={
            "email": attacker.email,
            "password": "password123",
        },
        follow_redirects=True,
    )

    response = client.get(f"/quizzes/{quiz.id}/take")

    assert response.status_code == 404


def test_owner_can_take_quiz(app, client, make_user, make_material):
    owner = make_user()
    material = make_material(owner)

    quiz = Quiz(
        material_id=material.id,
        title="Owner Quiz",
        difficulty="medium",
        status="ready",
    )

    db.session.add(quiz)
    db.session.commit()

    client.post(
        "/auth/login",
        data={
            "email": owner.email,
            "password": "password123",
        },
        follow_redirects=True,
    )

    response = client.get(f"/quizzes/{quiz.id}/take")

    assert response.status_code != 404

