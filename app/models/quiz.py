from datetime import datetime, timezone

from app.extensions import db


class Quiz(db.Model):
    __tablename__ = "quizzes"

    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey("study_materials.id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    difficulty = db.Column(db.String(10), nullable=False, default="medium")  # easy/medium/hard/mixed
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending/processing/ready/failed
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    material = db.relationship("StudyMaterial", backref=db.backref("quizzes", lazy=True, cascade="all, delete-orphan"))
    questions = db.relationship(
        "QuizQuestion", backref="quiz", lazy=True, cascade="all, delete-orphan",
        order_by="QuizQuestion.order_index",
    )
    attempts = db.relationship("QuizAttempt", backref="quiz", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Quiz {self.id}: {self.title}>"


class QuizQuestion(db.Model):
    __tablename__ = "quiz_questions"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False, index=True)

    question_type = db.Column(db.String(15), nullable=False)  # mcq / true_false / short / long
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=True)  # JSON array, MCQ only, e.g. ["A) ...", "B) ...", ...]
    correct_answer = db.Column(db.Text, nullable=False)  # letter/true|false for auto-graded; suggested text for self-graded
    order_index = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<QuizQuestion {self.id} ({self.question_type})>"


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    score = db.Column(db.Integer, nullable=True)  # computed once fully graded (including self-grading)
    total = db.Column(db.Integer, nullable=False)
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    owner = db.relationship("User", backref=db.backref("quiz_attempts", lazy=True, cascade="all, delete-orphan"))
    answers = db.relationship(
        "QuizAnswer", backref="attempt", lazy=True, cascade="all, delete-orphan",
        order_by="QuizAnswer.id",
    )

    def __repr__(self):
        return f"<QuizAttempt {self.id} for quiz {self.quiz_id}>"

    @property
    def score_percentage(self):
        if self.score is not None and self.total > 0:
            return round((self.score / self.total) * 100)
        return 0


class QuizAnswer(db.Model):
    __tablename__ = "quiz_answers"

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("quiz_attempts.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("quiz_questions.id"), nullable=False, index=True)

    submitted_answer = db.Column(db.Text, nullable=True)
    # NULL until graded: True/False set immediately for mcq/true_false,
    # set later via self-assessment for short/long.
    is_correct = db.Column(db.Boolean, nullable=True)

    question = db.relationship("QuizQuestion")

    def __repr__(self):
        return f"<QuizAnswer {self.id} for question {self.question_id}>"