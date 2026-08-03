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

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = os.environ.get("MAIL_PORT")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    # Upload constraints — one source of truth instead of every route
    # hardcoding its own limit later (Phase 3 will need this).
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB per request
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        INSTANCE_DIR, "learnio.db"
    )


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY")  # no unsafe fallback in prod
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")


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