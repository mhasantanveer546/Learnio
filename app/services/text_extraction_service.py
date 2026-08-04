from app.services.pdf_service import extract_text_from_pdf
from app.services.docx_service import extract_text_from_docx
from app.services.ppt_service import extract_text_from_pptx

EXTRACTORS = {
    "pdf": extract_text_from_pdf,
    "docx": extract_text_from_docx,
    "pptx": extract_text_from_pptx,
}


def extract_text(filepath, file_type):
    """Dispatches to the correct extractor based on file_type.

    txt files are handled inline (no library needed). Image types
    (jpg/png) intentionally raise — OCR extraction is Phase 9, not
    this phase; they stay 'pending' text-wise until then, but the
    file itself is still safely stored and viewable/downloadable.
    """
    if file_type == "txt":
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().strip()
        if not text:
            raise ValueError("This text file appears to be empty.")
        return text

    if file_type in EXTRACTORS:
        return EXTRACTORS[file_type](filepath)

    raise ValueError(
        f"Text extraction for '{file_type}' files isn't available yet "
        f"(image OCR is planned for a later phase)."
    )