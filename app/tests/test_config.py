from app.config import DevelopmentConfig, ProductionConfig, TestingConfig


def test_production_session_cookie_secure():
    assert ProductionConfig.SESSION_COOKIE_SECURE is True


def test_development_session_cookie_not_secure():
    assert DevelopmentConfig.SESSION_COOKIE_SECURE is False


def test_all_configs_have_httponly():
    assert DevelopmentConfig.SESSION_COOKIE_HTTPONLY is True
    assert ProductionConfig.SESSION_COOKIE_HTTPONLY is True
    assert TestingConfig.SESSION_COOKIE_HTTPONLY is True


def test_all_configs_have_samesite_lax():
    assert DevelopmentConfig.SESSION_COOKIE_SAMESITE == "Lax"
    assert ProductionConfig.SESSION_COOKIE_SAMESITE == "Lax"
    assert TestingConfig.SESSION_COOKIE_SAMESITE == "Lax"