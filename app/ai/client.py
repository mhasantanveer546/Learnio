import requests
from flask import current_app

DEFAULT_TIMEOUT_SECONDS = 15


def generate_content(prompt, max_retries=0, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
    """Call Gemini via the REST API using requests."""
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")

    # Your key only has Gemini 2.5/3.x models. gemini-1.5-flash is NOT available.
    models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-flash-latest"]

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096,
        }
    }

    for model_name in models:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent?key={api_key}"
        )

        try:
            resp = requests.post(url, json=payload, timeout=timeout_seconds)
            resp.raise_for_status()
            data = resp.json()

            if "candidates" in data and data["candidates"]:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                if not text:
                    raise RuntimeError("Gemini returned an empty response.")
                return text

            if "error" in data:
                raise RuntimeError(f"Gemini API error: {data['error']}")

            raise RuntimeError("Gemini returned an unexpected response.")

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else 0
            if status == 404 and model_name != models[-1]:
                current_app.logger.warning(
                    f"Gemini model {model_name} 404, trying fallback"
                )
                continue
            raise RuntimeError(f"Gemini API call failed: {status} {e}")

        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"Gemini API call failed: timed out after {timeout_seconds}s"
            )

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Gemini API call failed: {e}")

    raise RuntimeError("Gemini API call failed: no valid model found.")