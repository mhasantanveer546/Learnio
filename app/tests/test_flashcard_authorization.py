from app.extensions import db
from app.models import FlashcardSet, Flashcard


def test_non_owner_cannot_view_flashcards(
    app, client, make_user, make_material
):
    owner = make_user()
    attacker = make_user()

    material = make_material(owner)

    flashcard_set = FlashcardSet(
        material_id=material.id,
        status="ready",
    )
    db.session.add(flashcard_set)
    db.session.commit()

    client.post(
        "/auth/login",
        data={
            "email": attacker.email,
            "password": "password123",
        },
        follow_redirects=True,
    )

    response = client.get(f"/flashcards/{material.id}")

    assert response.status_code == 404


def test_owner_can_view_flashcards(
    app, client, make_user, make_material
):
    owner = make_user()

    material = make_material(owner)

    flashcard_set = FlashcardSet(
        material_id=material.id,
        status="ready",
    )
    db.session.add(flashcard_set)
    db.session.commit()

    client.post(
        "/auth/login",
        data={
            "email": owner.email,
            "password": "password123",
        },
        follow_redirects=True,
    )

    response = client.get(f"/flashcards/{material.id}")

    assert response.status_code != 404


def test_non_owner_cannot_mark_flashcard(
    app, client, make_user, make_material
):
    owner = make_user()
    attacker = make_user()

    material = make_material(owner)

    flashcard_set = FlashcardSet(
        material_id=material.id,
        status="ready",
    )
    db.session.add(flashcard_set)
    db.session.commit()

    card = Flashcard(
        set_id=flashcard_set.id,
        front_text="Question",
        back_text="Answer",
        difficulty="new",
        is_learned=False,
        order_index=0,
    )
    db.session.add(card)
    db.session.commit()

    client.post(
        "/auth/login",
        data={
            "email": attacker.email,
            "password": "password123",
        },
        follow_redirects=True,
    )

    response = client.post(
        f"/flashcards/card/{card.id}/mark",
        json={
            "is_learned": True,
            "difficulty": "easy",
        },
    )

    assert response.status_code == 404

    # Stronger assertion: make sure the card wasn't modified.
    db.session.refresh(card)
    assert card.is_learned is False
    assert card.difficulty == "new"


def test_owner_can_mark_flashcard(
    app, client, make_user, make_material
):
    owner = make_user()

    material = make_material(owner)

    flashcard_set = FlashcardSet(
        material_id=material.id,
        status="ready",
    )
    db.session.add(flashcard_set)
    db.session.commit()

    card = Flashcard(
        set_id=flashcard_set.id,
        front_text="Question",
        back_text="Answer",
        difficulty="new",
        is_learned=False,
        order_index=0,
    )
    db.session.add(card)
    db.session.commit()

    client.post(
        "/auth/login",
        data={
            "email": owner.email,
            "password": "password123",
        },
        follow_redirects=True,
    )

    response = client.post(
        f"/flashcards/card/{card.id}/mark",
        json={
            "is_learned": True,
            "difficulty": "easy",
        },
    )

    assert response.status_code == 200

    db.session.refresh(card)
    assert card.is_learned is True
    assert card.difficulty == "easy"