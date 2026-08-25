from unittest.mock import MagicMock, patch

import pytest
import requests

from app.ai.client import generate_content


def _setup_mock_app(monkeypatch):
    mock_app = MagicMock()
    mock_app.config = {"GEMINI_API_KEY": "fake-key"}
    monkeypatch.setattr("app.ai.client.current_app", mock_app)
    return mock_app


def _make_response(data, status_code=200):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = data
    mock_resp.raise_for_status.return_value = None
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

    with patch("app.ai.client.requests.post", return_value=_make_response(api_response)):
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

    with patch("app.ai.client.requests.post", return_value=_make_response(api_response)):
        with pytest.raises(RuntimeError, match="Gemini returned an empty response"):
            generate_content("test prompt")


def test_generate_content_api_error_in_body(monkeypatch):
    _setup_mock_app(monkeypatch)

    api_response = {
        "error": {"message": "API key invalid", "code": 400}
    }

    with patch("app.ai.client.requests.post", return_value=_make_response(api_response)):
        with pytest.raises(RuntimeError, match="Gemini API error"):
            generate_content("test prompt")


def test_generate_content_http_404_tries_fallback_model(monkeypatch):
    _setup_mock_app(monkeypatch)

    def side_effect(url, **kwargs):
        if "gemini-1.5-flash-latest" in url:
            raise requests.exceptions.HTTPError(
                response=MagicMock(status_code=404)
            )
        return _make_response({
            "candidates": [{
                "content": {"parts": [{"text": "Fallback success"}]}
            }]
        })

    with patch("app.ai.client.requests.post", side_effect=side_effect):
        result = generate_content("test prompt")
        assert result == "Fallback success"


def test_generate_content_http_404_on_last_model_raises(monkeypatch):
    _setup_mock_app(monkeypatch)

    def side_effect(url, **kwargs):
        raise requests.exceptions.HTTPError(
            response=MagicMock(status_code=404)
        )

    with patch("app.ai.client.requests.post", side_effect=side_effect):
        with pytest.raises(RuntimeError, match="404"):
            generate_content("test prompt")


def test_generate_content_http_429_raises(monkeypatch):
    _setup_mock_app(monkeypatch)

    def side_effect(url, **kwargs):
        raise requests.exceptions.HTTPError(
            response=MagicMock(status_code=429)
        )

    with patch("app.ai.client.requests.post", side_effect=side_effect):
        with pytest.raises(RuntimeError, match="429"):
            generate_content("test prompt")


def test_generate_content_timeout_raises(monkeypatch):
    _setup_mock_app(monkeypatch)

    with patch("app.ai.client.requests.post", side_effect=requests.exceptions.Timeout()):
        with pytest.raises(RuntimeError, match="timed out after"):
            generate_content("test prompt", timeout_seconds=10)


def test_generate_content_connection_error_raises(monkeypatch):
    _setup_mock_app(monkeypatch)

    with patch("app.ai.client.requests.post", side_effect=requests.exceptions.ConnectionError("Network down")):
        with pytest.raises(RuntimeError, match="Network down"):
            generate_content("test prompt")


def test_generate_content_no_api_key(monkeypatch):
    mock_app = MagicMock()
    mock_app.config = {"GEMINI_API_KEY": None}
    monkeypatch.setattr("app.ai.client.current_app", mock_app)

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY is not set"):
        generate_content("test prompt")