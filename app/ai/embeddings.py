import numpy as np
import google.generativeai as genai
from flask import current_app

_EMBED_MODEL = "models/gemini-embedding-001"


def _ensure_configured():
    """Configures the genai client from Flask's config, same source
    get_gemini_client() uses. Cheap to call repeatedly — configure()
    just sets the API key, it doesn't make a network call."""
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your .env file."
        )
    genai.configure(api_key=api_key)


def embed_texts(texts):
    """Embeds a list of text chunks (used when indexing a material)."""
    _ensure_configured()
    result = genai.embed_content(
        model=_EMBED_MODEL,
        content=texts,
        task_type="RETRIEVAL_DOCUMENT",
    )
    return np.array(result["embedding"], dtype=np.float32)


def embed_query(text):
    """Embeds a single query string (used when a student asks a question)."""
    _ensure_configured()
    result = genai.embed_content(
        model=_EMBED_MODEL,
        content=text,
        task_type="RETRIEVAL_QUERY",
    )
    return np.array(result["embedding"], dtype=np.float32)
