# app/models/__init__.py
from app.models.user import User
from app.models.subject import Subject
from app.models.study_material import StudyMaterial
from app.models.summary import Summary
from app.models.chat import ChatSession, ChatMessage
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizAnswer
from app.models.flashcard import FlashcardSet, Flashcard
from app.models.assignment import Assignment, Exam
from app.models.study_session import StudySession
from app.models.notification import Notification

__all__ = [
    "User", "Subject", "StudyMaterial", "Summary", "ChatSession", "ChatMessage",
    "Quiz", "QuizQuestion", "QuizAttempt", "QuizAnswer",
    "FlashcardSet", "Flashcard","Assignment", "Exam","StudySession","Notification"
]