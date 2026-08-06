from sentence_transformers import SentenceTransformer

# Loaded lazily, once, on first use — not at import time. Loading this
# model takes a moment; doing it eagerly would slow down every app
# startup even for requests that never touch chat.
_model = None


def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_texts(texts):
    """Embeds a list of text chunks (used when indexing a material)."""
    model = get_embedding_model()
    return model.encode(texts, convert_to_numpy=True, show_progress_bar=False)


def embed_query(text):
    """Embeds a single query string (used when a student asks a question)."""
    model = get_embedding_model()
    return model.encode([text], convert_to_numpy=True, show_progress_bar=False)[0]