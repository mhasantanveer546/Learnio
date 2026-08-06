from app.ai.client import generate_content
from app.ai.context_builder import build_prompt
from app.ai.vector_store import search_index


def answer_question(faiss_folder, subject_id, question, top_k=5):
    """The full RAG pipeline: retrieve → build constrained prompt →
    generate. Returns the answer plus which materials were cited."""
    retrieved = search_index(faiss_folder, subject_id, question, top_k=top_k)

    if not retrieved:
        return {
            "answer": "I don't have any indexed study materials for this subject yet. Upload and process some materials first.",
            "sources": [],
        }

    prompt = build_prompt(question, retrieved)
    answer = generate_content(prompt)

    # Dict comprehension dedupes by material_id while preserving one
    # display name per source — a student might retrieve 3 chunks from
    # the same PDF, but we only want to cite it once.
    sources = list({chunk["material_id"]: chunk["material_name"] for chunk in retrieved}.values())

    return {"answer": answer, "sources": sources}