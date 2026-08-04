import pdfplumber


def extract_text_from_pdf(filepath):
    """Extracts text from a PDF using pdfplumber (better table/layout
    handling than PyPDF2 alone). Returns a single string with pages
    joined by double newlines, or raises ValueError if nothing could
    be extracted (e.g. a scanned/image-only PDF with no text layer —
    that case is handled by OCR in Phase 9, not here)."""
    text_parts = []

    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    extracted = "\n\n".join(text_parts).strip()

    if not extracted:
        raise ValueError(
            "No extractable text found. This PDF may be scanned/image-based "
            "and requires OCR, which isn't available yet."
        )

    return extracted