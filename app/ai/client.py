import concurrent.futures
import time

import google.generativeai as genai
from flask import current_app

DEFAULT_TIMEOUT_SECONDS = 20


def get_gemini_client():
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")
    # FORCE REST transport — avoids grpc hangs on Vercel serverless
    genai.configure(api_key=api_key, transport="rest")
    return genai.GenerativeModel("gemini-2.5-flash")


def _is_transient_error(exc):
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
    """Runs model.generate_content in a worker thread with a hard timeout.
    With transport='rest', this uses HTTP under the hood — much more
    reliable on Vercel than grpc."""
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(model.generate_content, prompt)
    try:
        return future.result(timeout=timeout_seconds)
    except concurrent.futures.TimeoutError:
        executor.shutdown(wait=False)
        raise


def generate_content(prompt, max_retries=0, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
    """Single-entry point for Gemini. Zero retries on Vercel."""
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
                    f"total={total} model=gemini-2.5-flash"
                )

            return response.text

        except RuntimeError:
            raise

        except concurrent.futures.TimeoutError:
            if attempt < max_retries:
                wait = 2 ** attempt
                current_app.logger.warning(
                    f"Gemini call timed out after {timeout_seconds}s "
                    f"(attempt {attempt + 1}/{max_retries + 1}). Retrying in {wait}s..."
                )
                time.sleep(wait)
            else:
                raise RuntimeError(
                    f"Gemini API call failed: timed out after {timeout_seconds}s"
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