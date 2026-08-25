from unittest.mock import MagicMock, patch

import pytest

from app.ai.client import generate_content


def _setup_mock_app(monkeypatch):
    mock_app = MagicMock()
    mock_app.config = {"GEMINI_API_KEY": "fake-key"}
    monkeypatch.setattr("app.ai.client.current_app", mock_app)
    return mock_app


def test_generate_content_success(monkeypatch):
    _setup_mock_app(monkeypatch)

    mock_response = MagicMock()
    mock_response.text = "Hello from Gemini"

    with patch("app.ai.client.genai.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        MockClient.return_value = mock_client

        result = generate_content("test prompt")
        assert result == "Hello from Gemini"


def test_generate_content_empty_response(monkeypatch):
    _setup_mock_app(monkeypatch)

    mock_response = MagicMock()
    mock_response.text = ""

    with patch("app.ai.client.genai.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        MockClient.return_value = mock_client

        with pytest.raises(RuntimeError, match="Gemini returned an empty response"):
            generate_content("test prompt")


def test_generate_content_api_error(monkeypatch):
    _setup_mock_app(monkeypatch)

    with patch("app.ai.client.genai.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API key invalid")
        MockClient.return_value = mock_client

        with pytest.raises(RuntimeError, match="Gemini API call failed"):
            generate_content("test prompt")


def test_generate_content_no_api_key(monkeypatch):
    mock_app = MagicMock()
    mock_app.config = {"GEMINI_API_KEY": None}
    monkeypatch.setattr("app.ai.client.current_app", mock_app)

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY is not set"):
        generate_content("test prompt")