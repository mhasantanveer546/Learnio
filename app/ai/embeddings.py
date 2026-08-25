import numpy as np
import google.generativeai as genai
from flask import current_app

_EMBED_MODEL = "models/gemini-embedding-001"


def _ensure_configured():
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    # FORCE REST transport here too
    genai.configure(api_key=api_key, transport="rest")


def embed_texts(texts):
    _ensure_configured()
    result = genai.embed_content(
        model=_EMBED_MODEL,
        content=texts,
        task_type="RETRIEVAL_DOCUMENT",
    )
    return np.array(result["embedding"], dtype=np.float32)


def embed_query(text):
    _ensure_configured()
    result = genai.embed_content(
        model=_EMBED_MODEL,
        content=text,
        task_type="RETRIEVAL_QUERY",
    )
    return np.array(result["embedding"], dtype=np.float32)