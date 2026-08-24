import json

from app.extensions import db
from app.models import StudyMaterial, Quiz, QuizQuestion, QuizAttempt, QuizAnswer
from app.ai.client import generate_content
from app.ai.prompts import build_quiz_prompt


def _validate_quiz_json(parsed):
    if not isinstance(parsed, dict):
        raise ValueError(f"Expected JSON object, got {type(parsed).__name__}")

    if "questions" not in parsed:
        raise ValueError("Missing 'questions' key in quiz JSON")

    if not isinstance(parsed["questions"], list):
        raise ValueError(
            f"Expected 'questions' to be a list, got {type(parsed['questions']).__name__}"
        )

    for i, q in enumerate(parsed["questions"]):
        if not isinstance(q, dict):
            raise ValueError(f"Question {i} is not an object")

        required = ["type", "question", "correct_answer"]
        missing = [key for key in required if key not in q]
        if missing:
            raise ValueError(f"Question {i} missing required keys: {missing}")

        if q.get("type") == "mcq" and "options" not in q:
            raise ValueError(f"Question {i} (mcq) missing 'options'")

    return parsed


def generate_quiz(quiz_id, material_id, num_questions, question_types, difficulty):
    """Generates quiz with DB session refresh after Gemini call."""

    quiz = db.session.get(Quiz, quiz_id)
    if quiz is None:
        raise ValueError(f"Quiz {quiz_id} not found")

    material = db.session.get(StudyMaterial, material_id)
    if material is None or not material.extracted_text:
        quiz.status = "failed"
        db.session.commit()
        raise ValueError("This material has no extracted text yet.")

    quiz.difficulty = difficulty
    db.session.commit()

    extracted_text = material.extracted_text
    prompt = build_quiz_prompt(
        extracted_text, num_questions, question_types, difficulty
    )

    # Phase 2: Call Gemini
    try:
        raw_response = generate_content(prompt)
        cleaned = (
            raw_response.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        parsed = json.loads(cleaned)
        parsed = _validate_quiz_json(parsed)
        questions_data = parsed["questions"]

    except Exception as e:
        # FAILURE
        db.session.remove()
        quiz = db.session.get(Quiz, quiz_id)
        quiz.status = "failed"
        db.session.commit()
        raise RuntimeError(f"Quiz generation failed: {e}") from e

    # SUCCESS
    db.session.remove()
    quiz = db.session.get(Quiz, quiz_id)
    for index, q in enumerate(questions_data):
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_type=q["type"],
            question_text=q["question"],
            options=json.dumps(q["options"]) if q.get("options") else None,
            correct_answer=q["correct_answer"],
            order_index=index,
        )
        db.session.add(question)

    quiz.status = "ready"
    db.session.commit()
    return quiz


def start_attempt(quiz, user_id):
    attempt = QuizAttempt(quiz_id=quiz.id, user_id=user_id, total=len(quiz.questions))
    db.session.add(attempt)
    db.session.commit()
    return attempt


def submit_attempt(attempt, submitted_answers):
    score = 0
    for question in attempt.quiz.questions:
        submitted = submitted_answers.get(str(question.id), "").strip()

        is_correct = None
        if question.question_type in ("mcq", "true_false"):
            is_correct = (
                submitted.lower() == question.correct_answer.strip().lower()
            )
            if is_correct:
                score += 1

        answer = QuizAnswer(
            attempt_id=attempt.id,
            question_id=question.id,
            submitted_answer=submitted,
            is_correct=is_correct,
        )
        db.session.add(answer)

    attempt.score = score
    from datetime import datetime, timezone

    attempt.completed_at = datetime.now(timezone.utc)
    db.session.commit()
    return attempt


def self_grade_answer(answer, is_correct):
    answer.is_correct = is_correct
    db.session.commit()

    attempt = answer.attempt
    attempt.score = sum(1 for a in attempt.answers if a.is_correct)
    db.session.commit()
    return attempt