import numpy as np
from google import genai
from google.genai import types
from flask import current_app

_EMBED_MODEL = "gemini-embedding-001"


def _get_client():
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)


def embed_texts(texts):
    """Embeds a list of text chunks via google-genai REST API."""
    client = _get_client()
    result = client.models.embed_content(
        model=_EMBED_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
    )
    return np.array([e.values for e in result.embeddings], dtype=np.float32)


def embed_query(text):
    """Embeds a single query string via google-genai REST API."""
    client = _get_client()
    result = client.models.embed_content(
        model=_EMBED_MODEL,
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return np.array(result.embeddings[0].values, dtype=np.float32)