import time
import google.generativeai as genai
from flask import current_app


def get_gemini_client():
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-flash-latest")


def _is_transient_error(exc):
    """Determine if an exception is likely transient and worth retrying."""
    error_msg = str(exc).lower()
    transient_signals = [
        "rate limit", "quota", "resource exhausted",
        "timeout", "timed out",
        "temporarily unavailable", "service unavailable",
        "connection", "network",
        "internal server error",
        "503", "504", "429",
    ]
    return any(signal in error_msg for signal in transient_signals)


def generate_content(prompt, max_retries=3):
    """Single entry point for all Gemini calls in Learnio.
    Retries transient failures with exponential backoff.
    Logs token usage for cost tracking.
    """
    model = get_gemini_client()

    for attempt in range(max_retries + 1):
        try:
            response = model.generate_content(prompt)

            if not response.text:
                raise RuntimeError("Gemini returned an empty response.")

            # Log token usage for cost awareness
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
            # Our own errors (empty response) — don't retry
            raise

        except Exception as e:
            if _is_transient_error(e) and attempt < max_retries:
                wait = 2 ** attempt  # 1s, 2s, 4s
                current_app.logger.warning(
                    f"Gemini transient error (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                    f"Retrying in {wait}s..."
                )
                time.sleep(wait)
            else:
                raise RuntimeError(f"Gemini API call failed: {e}")

    raise RuntimeError("Gemini API call failed after maximum retries.")