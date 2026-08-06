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