import json
import pytest
from app.services.quiz_service import generate_quiz
from app.services.flashcard_service import generate_flashcards
from app.services.summary_service import generate_summary
from app.models import Quiz, FlashcardSet
from app.extensions import db


def test_generate_quiz_creates_questions(make_user, make_material, monkeypatch):
    owner = make_user()
    material = make_material(owner=owner, status="ready")
    material.extracted_text = "Sample text about math."
    db.session.commit()

    # The route creates the quiz row with status='processing' before
    # starting the background task. The service updates this existing row.
    quiz = Quiz(
        material_id=material.id,
        title="Quiz — test",
        status="processing",
    )
    db.session.add(quiz)
    db.session.commit()

    fake_response = json.dumps({
        "questions": [
            {
                "type": "mcq",
                "question": "What is 2+2?",
                "options": ["3", "4", "5", "6"],
                "correct_answer": "4"
            }
        ]
    })

    def mock_generate_content(prompt):
        return fake_response

    monkeypatch.setattr("app.services.quiz_service.generate_content", mock_generate_content)

    # Pass scalar IDs — same as the route now does
    quiz = generate_quiz(
        quiz_id=quiz.id,
        material_id=material.id,
        num_questions=1,
        question_types=["mcq"],
        difficulty="easy",
    )

    assert quiz.status == "ready"
    assert len(quiz.questions) == 1
    assert quiz.questions[0].question_text == "What is 2+2?"
    assert quiz.questions[0].correct_answer == "4"


def test_generate_quiz_handles_invalid_json(make_user, make_material, monkeypatch):
    owner = make_user()
    material = make_material(owner=owner, status="ready")
    material.extracted_text = "Sample text."
    db.session.commit()

    quiz = Quiz(
        material_id=material.id,
        title="Quiz — test",
        status="processing",
    )
    db.session.add(quiz)
    db.session.commit()

    quiz_id = quiz.id  # CAPTURE before service call — db.session.remove()
                       # in the service will detach this instance

    def mock_generate_content(prompt):
        return "not valid json"

    monkeypatch.setattr("app.services.quiz_service.generate_content", mock_generate_content)

    with pytest.raises(RuntimeError):
        generate_quiz(
            quiz_id=quiz_id,
            material_id=material.id,
            num_questions=1,
            question_types=["mcq"],
            difficulty="easy",
        )

    # Re-query from DB using captured ID
    quiz = db.session.get(Quiz, quiz_id)
    assert quiz.status == "failed"

def test_generate_flashcards_creates_cards(make_user, make_material, monkeypatch):
    owner = make_user()
    material = make_material(owner=owner, status="ready")
    material.extracted_text = "Sample text about science."
    db.session.commit()

    fake_response = json.dumps({
        "flashcards": [
            {"front": "What is H2O?", "back": "Water"}
        ]
    })

    def mock_generate_content(prompt):
        return fake_response

    monkeypatch.setattr("app.services.flashcard_service.generate_content", mock_generate_content)

    # Pass scalar ID — same as the route now does
    flashcard_set = generate_flashcards(material_id=material.id, num_cards=1)

    assert flashcard_set.status == "ready"
    assert len(flashcard_set.cards) == 1
    assert flashcard_set.cards[0].front_text == "What is H2O?"
    assert flashcard_set.cards[0].back_text == "Water"


def test_generate_summary_creates_summary(make_user, make_material, monkeypatch):
    owner = make_user()
    material = make_material(owner=owner, status="ready")
    material.extracted_text = "Sample text about history."
    db.session.commit()

    def mock_generate_content(prompt):
        return "This is a generated summary."

    monkeypatch.setattr("app.services.summary_service.generate_content", mock_generate_content)

    # Pass scalar ID — same as the route now does
    summary = generate_summary(material_id=material.id)

    assert summary.status == "ready"
    assert summary.content == "This is a generated summary."