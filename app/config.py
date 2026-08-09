import os
from dotenv import load_dotenv

load_dotenv()

# app/config.py -> app/ -> project root
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")


class Config:
    """Shared settings. Environment-specific classes below override
    only what actually differs between dev and prod."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-secret-for-dev-only")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    TESSERACT_CMD = os.environ.get("TESSERACT_CMD")  # optional — only needed if tesseract isn't on system PATH
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = os.environ.get("MAIL_PORT")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    # Upload constraints — one source of truth instead of every route
    # hardcoding its own limit.
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB per request
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

    # Phase 5 — per-subject FAISS indexes + their metadata JSON files
    # live here. Matches the original project spec's file structure
    # (app/static/faiss_index/), kept gitignored since these are
    # generated artifacts, not source.
    FAISS_INDEX_FOLDER = os.path.join(BASE_DIR, "app", "static", "faiss_index")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        INSTANCE_DIR, "learnio.db"
    )


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY")

    _database_url = os.environ.get("DATABASE_URL")
    if _database_url and _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _database_url

class TestingConfig(Config):
    """Isolated in-memory DB so pytest never touches the real learnio.db."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}