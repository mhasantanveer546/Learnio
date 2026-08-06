# app/models/__init__.py
from app.models.user import User
from app.models.subject import Subject
from app.models.study_material import StudyMaterial
from app.models.summary import Summary
# app/models/__init__.py
from app.models.chat import ChatSession, ChatMessage
# add both to __all__

__all__ = ["User", "Subject", "StudyMaterial", "Summary","ChatSession", "ChatMessage"]