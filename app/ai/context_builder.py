import re


def chunk_text(text, chunk_size=800, overlap=100):
    """Splits text into overlapping chunks, breaking on sentence
    boundaries rather than mid-sentence. The overlap means a fact
    that lands near a chunk boundary still appears fully in at least
    one chunk, instead of being cut in half and lost from both."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) <= chunk_size:
            current += (" " if current else "") + sentence
        else:
            if current:
                chunks.append(current.strip())
            overlap_text = current[-overlap:] if len(current) > overlap else current
            current = overlap_text + " " + sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks


def build_prompt(question, retrieved_chunks):
    """Builds the RAG prompt — this is where 'answer ONLY using
    uploaded material' (per the spec) is actually enforced, at the
    prompt level."""
    context_blocks = [
        f"[Source: {chunk['material_name']}]\n{chunk['text']}"
        for chunk in retrieved_chunks
    ]
    context = "\n\n---\n\n".join(context_blocks)

    return f"""You are a study assistant answering a student's question using ONLY the study material provided below.

Rules:
- Answer using ONLY the information in the provided context.
- If the answer isn't in the context, say "I couldn't find this in your uploaded materials" — do not use outside knowledge.
- Cite which source(s) you used when relevant.
- Be concise and clear.

CONTEXT:
{context}

STUDENT QUESTION:
{question}
"""

def build_solve_prompt(question, retrieved_chunks):
    """Solve Mode — unlike build_prompt (strict RAG, retrieval-only),
    this allows Gemini to reason and generate original solutions
    (e.g. write code, work through a problem), using the material as
    context rather than as the only permitted source of truth.
    Still grounded in what was uploaded, but not restricted to
    refusing when the material only describes a problem rather than
    containing its solution."""
    context_blocks = [
        f"[From: {chunk['material_name']}]\n{chunk['text']}"
        for chunk in retrieved_chunks
    ]
    context = "\n\n---\n\n".join(context_blocks) if context_blocks else "(No directly matching material found — use your own knowledge to help.)"

    return f"""You are a helpful study assistant helping a university student with an assignment or problem.

The student's uploaded material is provided below for context — it may describe a problem, assignment, or question. Unlike a strict lookup tool, you SHOULD use your own knowledge and reasoning to actually help solve the problem, write code, or work through the question — don't just describe what the material says.

Guidelines:
- If the material describes a problem/assignment, actually attempt to solve it or help complete it.
- Reference the material's specific requirements (e.g. constraints, expected format) so your answer fits what was actually asked.
- Be clear and well-structured; use code blocks for code.
- It's fine to go beyond what's literally written in the material — that's the point of this mode.

STUDENT'S MATERIAL (for context):
{context}

STUDENT QUESTION:
{question}
"""