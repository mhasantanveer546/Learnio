import io
import json
import os
import tempfile

import faiss
import numpy as np

from app.ai.embeddings import embed_texts, embed_query
from app.services.storage_service import upload_file_obj, download_to_temp, delete_file

INDEX_DIMENSION = 384


def _index_key(material_id):
    return f"faiss/material_{material_id}.index"


def _meta_key(material_id):
    return f"faiss/material_{material_id}_meta.json"


def build_material_index(material_id, material_name, chunks):
    """Builds a material's FAISS index in memory, then uploads both
    the index file and its metadata JSON to R2 — same object storage
    as everything else, so nothing here depends on local disk
    persisting between requests."""
    vectors = embed_texts(chunks)

    index = faiss.IndexFlatL2(INDEX_DIMENSION)
    index.add(np.array(vectors).astype("float32"))

    metadata = [{"material_id": material_id, "material_name": material_name, "text": chunk} for chunk in chunks]

    # FAISS's own API only knows how to write to a real file path, not
    # an in-memory buffer directly — so we write to a temp file first,
    # then upload that temp file's bytes to R2, then clean up. This is
    # "processing scratch space" exactly like extraction's temp files,
    # not permanent storage.
    fd, temp_path = tempfile.mkstemp(suffix=".index")
    os.close(fd)
    try:
        faiss.write_index(index, temp_path)
        with open(temp_path, "rb") as f:
            upload_file_obj(f, _index_key(material_id))
    finally:
        os.remove(temp_path)

    meta_bytes = json.dumps(metadata).encode("utf-8")
    upload_file_obj(io.BytesIO(meta_bytes), _meta_key(material_id))


def search_index(material_id, query, top_k=5):
    """Downloads a material's index + metadata from R2 to temp files,
    searches, cleans up. Every search pays a small download cost —
    acceptable given index files are small (a few hundred KB at most
    for typical study material chunk counts) and chat isn't a
    high-frequency operation like every keystroke."""
    try:
        index_temp = download_to_temp(_index_key(material_id), suffix=".index")
        meta_temp = download_to_temp(_meta_key(material_id), suffix=".json")
    except Exception:
        # Index doesn't exist yet (material never indexed, or indexing
        # failed) — same "no results" behavior as before, not an error.
        return []

    try:
        index = faiss.read_index(index_temp)
        with open(meta_temp, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        if index.ntotal == 0:
            return []

        query_vector = np.array([embed_query(query)]).astype("float32")
        _, indices = index.search(query_vector, min(top_k, index.ntotal))

        return [metadata[idx] for idx in indices[0] if idx != -1]
    finally:
        os.remove(index_temp)
        os.remove(meta_temp)


def delete_material_index(material_id):
    """Deletes both R2 objects for a material's index — called when
    the material itself is deleted."""
    for key in (_index_key(material_id), _meta_key(material_id)):
        try:
            delete_file(key)
        except Exception:
            pass  # object may not exist (e.g. material was never successfully indexed) — not a real error