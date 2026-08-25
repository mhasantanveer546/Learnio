import json
import urllib.request
import urllib.error
from flask import current_app

DEFAULT_TIMEOUT_SECONDS = 45


def generate_content(prompt, max_retries=0, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
    """Call Gemini via the REST API. Avoids grpc/threading issues on Vercel."""
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")

    # Try model names in order of preference
    models = ["gemini-1.5-flash", "gemini-flash-latest"]

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8192,
        }
    }).encode("utf-8")

    for model_name in models:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent?key={api_key}"
        )

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            if "candidates" in data and data["candidates"]:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                if not text:
                    raise RuntimeError("Gemini returned an empty response.")
                return text

            if "error" in data:
                raise RuntimeError(f"Gemini API error: {data['error']}")

            raise RuntimeError("Gemini returned an unexpected response.")

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            # 404 means model name wrong — try next one
            if e.code == 404 and model_name != models[-1]:
                continue
            raise RuntimeError(f"Gemini API call failed: {e.code} {e.reason} — {body}")

        except urllib.error.URLError as e:
            raise RuntimeError(f"Gemini API call failed: {e.reason}")

        except TimeoutError:
            raise RuntimeError(
                f"Gemini API call failed: timed out after {timeout_seconds}s"
            )

    raise RuntimeError("Gemini API call failed: no valid model found.")