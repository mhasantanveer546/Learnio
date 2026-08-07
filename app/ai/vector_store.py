import os
import json

import faiss
import numpy as np

from app.ai.embeddings import embed_texts, embed_query

INDEX_DIMENSION = 384  # matches all-MiniLM-L6-v2's output size


def _index_path(faiss_folder, material_id):
    return os.path.join(faiss_folder, f"material_{material_id}.index")


def _meta_path(faiss_folder, material_id):
    return os.path.join(faiss_folder, f"material_{material_id}_meta.json")


def build_material_index(faiss_folder, material_id, material_name, chunks):
    """Builds a fresh, self-contained index for a single material.
    Unlike the old per-subject scheme, this always creates from
    scratch — a material's index never needs incremental appends,
    since it's only ever indexed once (or fully rebuilt on retry)."""
    os.makedirs(faiss_folder, exist_ok=True)

    index = faiss.IndexFlatL2(INDEX_DIMENSION)
    vectors = embed_texts(chunks)
    index.add(np.array(vectors).astype("float32"))

    metadata = [{"material_id": material_id, "material_name": material_name, "text": chunk} for chunk in chunks]

    faiss.write_index(index, _index_path(faiss_folder, material_id))
    with open(_meta_path(faiss_folder, material_id), "w", encoding="utf-8") as f:
        json.dump(metadata, f)


def search_index(faiss_folder, material_id, query, top_k=5):
    """Returns the top_k most relevant chunks from a single material's
    index for a given query."""
    index_path = _index_path(faiss_folder, material_id)
    meta_path = _meta_path(faiss_folder, material_id)

    if not os.path.exists(index_path) or not os.path.exists(meta_path):
        return []

    index = faiss.read_index(index_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    if index.ntotal == 0:
        return []

    query_vector = np.array([embed_query(query)]).astype("float32")
    _, indices = index.search(query_vector, min(top_k, index.ntotal))

    return [metadata[idx] for idx in indices[0] if idx != -1]


def delete_material_index(faiss_folder, material_id):
    """Cleanly removes a material's index files. Called when a
    material is deleted — this is the exact problem the old
    per-subject scheme couldn't solve (FAISS can't delete individual
    vectors from a shared index); per-material indexing makes
    deletion trivial: just delete the two files."""
    for path in (_index_path(faiss_folder, material_id), _meta_path(faiss_folder, material_id)):
        if os.path.exists(path):
            os.remove(path)