import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from app.ai.client import generate_content


def _setup_mock_app(monkeypatch):
    mock_app = MagicMock()
    mock_app.config = {"GEMINI_API_KEY": "fake-key"}
    monkeypatch.setattr("app.ai.client.current_app", mock_app)
    return mock_app


def _make_response(data, status=200):
    """Build a mock urllib response."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(data).encode("utf-8")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = lambda *args: None
    return mock_resp


def test_generate_content_success(monkeypatch):
    _setup_mock_app(monkeypatch)

    api_response = {
        "candidates": [{
            "content": {
                "parts": [{"text": "Hello from Gemini"}]
            }
        }]
    }

    with patch("app.ai.client.urllib.request.urlopen", return_value=_make_response(api_response)):
        result = generate_content("test prompt")
        assert result == "Hello from Gemini"


def test_generate_content_empty_response(monkeypatch):
    _setup_mock_app(monkeypatch)

    api_response = {
        "candidates": [{
            "content": {
                "parts": [{"text": ""}]
            }
        }]
    }

    with patch("app.ai.client.urllib.request.urlopen", return_value=_make_response(api_response)):
        with pytest.raises(RuntimeError, match="Gemini returned an empty response"):
            generate_content("test prompt")


def test_generate_content_api_error_in_body(monkeypatch):
    _setup_mock_app(monkeypatch)

    api_response = {
        "error": {"message": "API key invalid", "code": 400}
    }

    with patch("app.ai.client.urllib.request.urlopen", return_value=_make_response(api_response)):
        with pytest.raises(RuntimeError, match="Gemini API error"):
            generate_content("test prompt")


def test_generate_content_http_404_tries_fallback_model(monkeypatch):
    _setup_mock_app(monkeypatch)

    def side_effect(req, **kwargs):
        if "gemini-1.5-flash" in req.full_url:
            raise urllib.error.HTTPError(
                req.full_url, 404, "Not Found", {},
                io.BytesIO(b'{"error": {"message": "not found"}}')
            )
        return _make_response({
            "candidates": [{
                "content": {"parts": [{"text": "Fallback success"}]}
            }]
        })

    with patch("app.ai.client.urllib.request.urlopen", side_effect=side_effect):
        result = generate_content("test prompt")
        assert result == "Fallback success"


def test_generate_content_http_404_on_last_model_raises(monkeypatch):
    _setup_mock_app(monkeypatch)

    def side_effect(req, **kwargs):
        raise urllib.error.HTTPError(
            req.full_url, 404, "Not Found", {},
            io.BytesIO(b'{"error": {"message": "not found"}}')
        )

    with patch("app.ai.client.urllib.request.urlopen", side_effect=side_effect):
        with pytest.raises(RuntimeError, match="404"):
            generate_content("test prompt")


def test_generate_content_http_429_raises(monkeypatch):
    _setup_mock_app(monkeypatch)

    def side_effect(req, **kwargs):
        raise urllib.error.HTTPError(
            req.full_url, 429, "Too Many Requests", {},
            io.BytesIO(b'{"error": {"message": "rate limited"}}')
        )

    with patch("app.ai.client.urllib.request.urlopen", side_effect=side_effect):
        with pytest.raises(RuntimeError, match="429"):
            generate_content("test prompt")


def test_generate_content_url_error_raises(monkeypatch):
    _setup_mock_app(monkeypatch)

    with patch("app.ai.client.urllib.request.urlopen", side_effect=urllib.error.URLError("Network down")):
        with pytest.raises(RuntimeError, match="Network down"):
            generate_content("test prompt")


def test_generate_content_timeout_raises(monkeypatch):
    _setup_mock_app(monkeypatch)

    with patch("app.ai.client.urllib.request.urlopen", side_effect=TimeoutError()):
        with pytest.raises(RuntimeError, match="timed out after"):
            generate_content("test prompt", timeout_seconds=10)


def test_generate_content_no_api_key(monkeypatch):
    mock_app = MagicMock()
    mock_app.config = {"GEMINI_API_KEY": None}
    monkeypatch.setattr("app.ai.client.current_app", mock_app)

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY is not set"):
        generate_content("test prompt")