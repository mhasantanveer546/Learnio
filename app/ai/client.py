import json
import socket
import urllib.request
import urllib.error
from flask import current_app

DEFAULT_TIMEOUT_SECONDS = 30


def generate_content(prompt, max_retries=0, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")

    models = ["gemini-1.5-flash", "gemini-flash-latest"]

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096,
        }
    }).encode("utf-8")

    current_app.logger.info(
        f"Gemini request: {len(payload)} bytes, {len(prompt)} chars prompt"
    )

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

        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout_seconds)

        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            socket.setdefaulttimeout(old_timeout)

            if "candidates" in data and data["candidates"]:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                if not text:
                    raise RuntimeError("Gemini returned an empty response.")
                current_app.logger.info(
                    f"Gemini success: {len(text)} chars response"
                )
                return text

            if "error" in data:
                raise RuntimeError(f"Gemini API error: {data['error']}")

            raise RuntimeError("Gemini returned an unexpected response.")

        except urllib.error.HTTPError as e:
            socket.setdefaulttimeout(old_timeout)
            body = ""
            try:
                if e.fp is not None:
                    body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                body = str(e)

            if e.code == 404 and model_name != models[-1]:
                current_app.logger.warning(
                    f"Gemini model {model_name} 404, trying fallback"
                )
                continue
            raise RuntimeError(f"Gemini API call failed: {e.code} {e.reason} — {body}")

        except urllib.error.URLError as e:
            socket.setdefaulttimeout(old_timeout)
            raise RuntimeError(f"Gemini API call failed: {e.reason}")

        except TimeoutError:
            socket.setdefaulttimeout(old_timeout)
            raise RuntimeError(
                f"Gemini API call failed: timed out after {timeout_seconds}s"
            )

        except Exception as e:
            socket.setdefaulttimeout(old_timeout)
            raise RuntimeError(f"Gemini API call failed: {e}")

    raise RuntimeError("Gemini API call failed: no valid model found.")