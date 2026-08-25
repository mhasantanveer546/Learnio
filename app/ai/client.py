from google import genai
from google.genai import types
from flask import current_app

DEFAULT_TIMEOUT_SECONDS = 15


def generate_content(prompt, max_retries=0, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
    """Call Gemini via the new google-genai SDK (REST by default).
    This is the only SDK that works with this API key's model access."""
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")

    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=timeout_seconds * 1000))

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=4096,
            ),
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        return response.text

    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}") from e