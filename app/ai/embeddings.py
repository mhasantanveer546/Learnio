import numpy as np
import requests
from flask import current_app

_EMBED_MODEL = "models/gemini-embedding-001"


def _get_api_key():
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    return api_key


def embed_texts(texts):
    """Embeds a list of text chunks via REST API."""
    api_key = _get_api_key()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/"
        f"{_EMBED_MODEL}:batchEmbedContents?key={api_key}"
    )

    requests_data = []
    for text in texts:
        requests_data.append({
            "model": _EMBED_MODEL,
            "content": {"parts": [{"text": text}]},
            "taskType": "RETRIEVAL_DOCUMENT",
        })

    resp = requests.post(url, json={"requests": requests_data}, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    embeddings = [
        np.array(r["embedding"]["values"], dtype=np.float32)
        for r in data.get("embeddings", [])
    ]
    return np.array(embeddings)


def embed_query(text):
    """Embeds a single query string via REST API."""
    api_key = _get_api_key()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/"
        f"{_EMBED_MODEL}:embedContent?key={api_key}"
    )

    resp = requests.post(url, json={
        "model": _EMBED_MODEL,
        "content": {"parts": [{"text": text}]},
        "taskType": "RETRIEVAL_QUERY",
    }, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    return np.array(data["embedding"]["values"], dtype=np.float32)