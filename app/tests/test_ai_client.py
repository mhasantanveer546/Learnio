import concurrent.futures
import pytest
from unittest.mock import MagicMock

from app.ai.client import generate_content, _is_transient_error, _generate_with_timeout


def test_is_transient_error_detects_rate_limit():
    assert _is_transient_error(Exception("Rate limit exceeded")) is True


def test_is_transient_error_detects_timeout():
    assert _is_transient_error(Exception("Request timeout")) is True


def test_is_transient_error_detects_deadline_exceeded():
    assert _is_transient_error(Exception("Deadline of 30.0s exceeded")) is True


def test_is_transient_error_detects_503():
    assert _is_transient_error(Exception("503 Service Unavailable")) is True


def test_is_transient_error_rejects_permanent():
    assert _is_transient_error(Exception("Invalid API key")) is False


def test_is_transient_error_rejects_random():
    assert _is_transient_error(Exception("Something went wrong")) is False


def _setup_mock_app(monkeypatch):
    mock_app = MagicMock()
    mock_app.config = {"GEMINI_API_KEY": "fake-key"}
    monkeypatch.setattr("app.ai.client.current_app", mock_app)
    monkeypatch.setattr("app.ai.client.time.sleep", lambda x: None)
    monkeypatch.setattr("app.ai.client.genai.configure", lambda **kwargs: None)
    return mock_app


def _make_mock_model(response_text="Success", usage_metadata=None, side_effect=None):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_response.usage_metadata = usage_metadata

    if side_effect:
        mock_model.generate_content.side_effect = side_effect
    else:
        mock_model.generate_content.return_value = mock_response

    return mock_model


def test_generate_content_retries_transient_errors(monkeypatch):
    _setup_mock_app(monkeypatch)

    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise Exception("Rate limit exceeded")
        mock_response = MagicMock()
        mock_response.text = "Success after retry"
        mock_response.usage_metadata = None
        return mock_response

    mock_model = _make_mock_model(side_effect=side_effect)
    monkeypatch.setattr("app.ai.client.genai.GenerativeModel", lambda name: mock_model)

    result = generate_content("test prompt", max_retries=3, timeout_seconds=30)
    assert result == "Success after retry"
    assert call_count == 3


def test_generate_content_raises_after_max_retries(monkeypatch):
    _setup_mock_app(monkeypatch)

    mock_model = _make_mock_model(side_effect=Exception("Service unavailable"))
    monkeypatch.setattr("app.ai.client.genai.GenerativeModel", lambda name: mock_model)

    with pytest.raises(RuntimeError, match="Gemini API call failed"):
        generate_content("test prompt", max_retries=2, timeout_seconds=30)

    assert mock_model.generate_content.call_count == 3


def test_generate_content_no_retry_on_permanent_error(monkeypatch):
    _setup_mock_app(monkeypatch)

    mock_model = _make_mock_model(side_effect=Exception("Invalid API key"))
    monkeypatch.setattr("app.ai.client.genai.GenerativeModel", lambda name: mock_model)

    with pytest.raises(RuntimeError, match="Gemini API call failed"):
        generate_content("test prompt", max_retries=3, timeout_seconds=30)

    assert mock_model.generate_content.call_count == 1


def test_generate_content_retries_on_timeout(monkeypatch):
    _setup_mock_app(monkeypatch)

    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise concurrent.futures.TimeoutError()
        mock_response = MagicMock()
        mock_response.text = "Success after timeout"
        mock_response.usage_metadata = None
        return mock_response

    mock_model = _make_mock_model(side_effect=side_effect)
    monkeypatch.setattr("app.ai.client.genai.GenerativeModel", lambda name: mock_model)

    result = generate_content("test prompt", max_retries=3, timeout_seconds=30)
    assert result == "Success after timeout"
    assert call_count == 3


def test_generate_content_raises_after_timeout_retries(monkeypatch):
    _setup_mock_app(monkeypatch)

    mock_model = _make_mock_model(side_effect=concurrent.futures.TimeoutError)
    monkeypatch.setattr("app.ai.client.genai.GenerativeModel", lambda name: mock_model)

    with pytest.raises(RuntimeError, match="Gemini API call failed"):
        generate_content("test prompt", max_retries=2, timeout_seconds=30)

    assert mock_model.generate_content.call_count == 3


def test_generate_content_logs_token_usage(monkeypatch):
    mock_app = _setup_mock_app(monkeypatch)

    mock_meta = MagicMock()
    mock_meta.prompt_token_count = 100
    mock_meta.candidates_token_count = 50

    mock_model = _make_mock_model(response_text="Response text", usage_metadata=mock_meta)
    monkeypatch.setattr("app.ai.client.genai.GenerativeModel", lambda name: mock_model)

    generate_content("test prompt", timeout_seconds=30)

    log_calls = [
        call for call in mock_app.logger.info.call_args_list
        if "Gemini usage" in str(call)
    ]
    assert len(log_calls) == 1
    assert "prompt=100" in str(log_calls[0])
    assert "completion=50" in str(log_calls[0])
    assert "total=150" in str(log_calls[0])


def test_generate_content_empty_response_not_retried(monkeypatch):
    _setup_mock_app(monkeypatch)

    mock_model = _make_mock_model(response_text="")
    monkeypatch.setattr("app.ai.client.genai.GenerativeModel", lambda name: mock_model)

    with pytest.raises(RuntimeError, match="Gemini returned an empty response"):
        generate_content("test prompt", max_retries=3, timeout_seconds=30)

    assert mock_model.generate_content.call_count == 1