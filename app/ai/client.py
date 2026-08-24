import concurrent.futures
import time

import google.generativeai as genai
from flask import current_app

DEFAULT_TIMEOUT_SECONDS = 15  # comfortably under Vercel's 60s function limit


def get_gemini_client():
    """Configures and returns a Gemini model instance. Reads the API
    key from app config (not directly from os.environ) so it respects
    Flask's config system — same pattern as every other setting in
    this app, and testable via TestingConfig later if needed."""
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your .env file."
        )
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-flash-latest")


def _is_transient_error(exc):
    """Heuristic: is this exception likely a transient Gemini-side
    failure (worth retrying) or a permanent one (retrying won't help,
    e.g. bad API key, malformed request)? String matching, since the
    SDK doesn't give us clean typed exceptions to catch on. Note:
    concurrent.futures.TimeoutError is handled separately, NOT here —
    its message is empty, so string matching can't see it."""
    error_msg = str(exc).lower()
    transient_signals = [
        "rate limit", "quota", "resource exhausted",
        "timeout", "timed out", "deadline",
        "temporarily unavailable", "service unavailable",
        "connection", "network",
        "internal server error",
        "503", "504", "429",
    ]
    return any(signal in error_msg for signal in transient_signals)


def _generate_with_timeout(model, prompt, timeout_seconds):
    """Runs model.generate_content in a worker thread and enforces a
    hard wall-clock timeout via concurrent.futures, rather than relying
    solely on the Gemini SDK's own request_options timeout (not
    consistently honored across SDK versions/transports — and this SDK
    is already deprecated, so we don't lean on its internals).

    On Vercel specifically, this matters: a hang here would otherwise
    silently eat the entire 60s function budget with no chance for our
    own code to fail cleanly and mark a resource 'failed' first."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(model.generate_content, prompt)
        return future.result(timeout=timeout_seconds)


def generate_content(prompt, max_retries=1, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
    """The single entry point every service in this app should use to
    talk to Gemini. Centralizing this here means: model choice, retry
    logic, timeout enforcement, and error handling all live in exactly
    one place.

    Retries transient failures (rate limits, timeouts, 5xx) with
    exponential backoff (1s, 2s, 4s...). Permanent failures (bad API
    key, invalid request) are NOT retried.

    Logs token usage on every successful call for cost awareness.

    Raises RuntimeError on any failure (after retries are exhausted,
    or immediately for permanent errors) — callers catch this and turn
    it into a 'failed' status, same pattern as text extraction."""
    model = get_gemini_client()

    for attempt in range(max_retries + 1):
        try:
            response = _generate_with_timeout(model, prompt, timeout_seconds)

            if not response.text:
                raise RuntimeError("Gemini returned an empty response.")

            if hasattr(response, "usage_metadata") and response.usage_metadata:
                meta = response.usage_metadata
                prompt_tokens = getattr(meta, "prompt_token_count", 0)
                completion_tokens = getattr(meta, "candidates_token_count", 0)
                total = prompt_tokens + completion_tokens
                current_app.logger.info(
                    f"Gemini usage: prompt={prompt_tokens} completion={completion_tokens} "
                    f"total={total} model=gemini-flash-latest"
                )

            return response.text

        except RuntimeError:
            # Our own error (empty response) — not a Gemini SDK/timeout
            # exception, so treat as permanent: don't retry.
            raise

        except concurrent.futures.TimeoutError:
            # Always transient, unconditionally — a bare TimeoutError()
            # has no message for _is_transient_error to match against.
            if attempt < max_retries:
                wait = 2 ** attempt
                current_app.logger.warning(
                    f"Gemini call timed out after {timeout_seconds}s "
                    f"(attempt {attempt + 1}/{max_retries + 1}). Retrying in {wait}s..."
                )
                time.sleep(wait)
            else:
                raise RuntimeError(
                    f"Gemini API call failed: timed out after {timeout_seconds}s "
                    f"on all {max_retries + 1} attempts"
                )

        except Exception as e:
            if _is_transient_error(e) and attempt < max_retries:
                wait = 2 ** attempt
                current_app.logger.warning(
                    f"Gemini transient error (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                    f"Retrying in {wait}s..."
                )
                time.sleep(wait)
            else:
                raise RuntimeError(f"Gemini API call failed: {e}")

    raise RuntimeError("Gemini API call failed after maximum retries.")