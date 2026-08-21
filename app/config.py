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
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,   # test each connection before using it; auto-reconnect if stale
        "pool_recycle": 280,     # recycle connections before Neon's own idle timeout kicks in
    }
    # Session cookie security — explicit is better than implicit
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False   # overridden in ProductionConfig

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

    
    R2_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL")
    R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
    R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
    R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME")
    ASSET_VERSION = 2

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        INSTANCE_DIR, "learnio.db"
    )


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SESSION_COOKIE_SECURE = True   #<-- this added

    _database_url = os.environ.get("DATABASE_URL")
    if _database_url and _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _database_url

class TestingConfig(Config):
    """Isolated in-memory DB so pytest never touches the real learnio.db."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False   # ← ADD THIS

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}