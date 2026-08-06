import os
import json

import faiss
import numpy as np

from app.ai.embeddings import embed_texts, embed_query

INDEX_DIMENSION = 384  # matches all-MiniLM-L6-v2's output size


def _index_path(faiss_folder, subject_id):
    return os.path.join(faiss_folder, f"subject_{subject_id}.index")


def _meta_path(faiss_folder, subject_id):
    return os.path.join(faiss_folder, f"subject_{subject_id}_meta.json")


def load_or_create_index(faiss_folder, subject_id):
    os.makedirs(faiss_folder, exist_ok=True)
    index_path = _index_path(faiss_folder, subject_id)
    meta_path = _meta_path(faiss_folder, subject_id)

    if os.path.exists(index_path) and os.path.exists(meta_path):
        index = faiss.read_index(index_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        index = faiss.IndexFlatL2(INDEX_DIMENSION)
        metadata = []  # metadata[i] describes the chunk stored at vector i

    return index, metadata


def save_index(faiss_folder, subject_id, index, metadata):
    os.makedirs(faiss_folder, exist_ok=True)
    faiss.write_index(index, _index_path(faiss_folder, subject_id))
    with open(_meta_path(faiss_folder, subject_id), "w", encoding="utf-8") as f:
        json.dump(metadata, f)


def add_material_to_index(faiss_folder, subject_id, material_id, material_name, chunks):
    """Embeds and appends a material's chunks to its subject's index.
    Incremental — existing vectors from other materials in the same
    subject are untouched, so uploading material #4 doesn't require
    re-embedding materials #1–3."""
    index, metadata = load_or_create_index(faiss_folder, subject_id)

    vectors = embed_texts(chunks)
    index.add(np.array(vectors).astype("float32"))

    for chunk in chunks:
        metadata.append({"material_id": material_id, "material_name": material_name, "text": chunk})

    save_index(faiss_folder, subject_id, index, metadata)


def search_index(faiss_folder, subject_id, query, top_k=5):
    """Returns the top_k most relevant chunks for a query, each
    carrying its source material's name for citation."""
    index, metadata = load_or_create_index(faiss_folder, subject_id)

    if index.ntotal == 0:
        return []

    query_vector = np.array([embed_query(query)]).astype("float32")
    _, indices = index.search(query_vector, min(top_k, index.ntotal))

    return [metadata[idx] for idx in indices[0] if idx != -1]