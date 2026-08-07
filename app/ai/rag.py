from app.ai.client import generate_content
from app.ai.context_builder import build_prompt, build_solve_prompt
from app.ai.vector_store import search_index


def answer_question(faiss_folder, material_id, question, mode="study", top_k=5):
    """RAG pipeline scoped to a single material.

    mode="study" (default): strictly grounded, refuses to answer
    beyond what's retrieved — the original, trustworthy behavior.
    mode="solve": uses the material as context but allows Gemini to
    reason/generate solutions beyond what's literally in the text."""
    retrieved = search_index(faiss_folder, material_id, question, top_k=top_k)

    if not retrieved and mode == "study":
        return {
            "answer": "This material hasn't been indexed yet, or has no searchable content.",
            "sources": [],
        }

    prompt = build_solve_prompt(question, retrieved) if mode == "solve" else build_prompt(question, retrieved)
    answer = generate_content(prompt)

    sources = list({chunk["material_id"]: chunk["material_name"] for chunk in retrieved}.values())

    return {"answer": answer, "sources": sources}