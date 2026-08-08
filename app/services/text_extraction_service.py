from app.services.pdf_service import extract_text_from_pdf
from app.services.docx_service import extract_text_from_docx
from app.services.ppt_service import extract_text_from_pptx
from app.services.ocr_service import extract_text_from_image

EXTRACTORS = {
    "pdf": extract_text_from_pdf,
    "docx": extract_text_from_docx,
    "pptx": extract_text_from_pptx,
    "jpg": extract_text_from_image,
    "png": extract_text_from_image,
}


def extract_text(filepath, file_type):
    """Dispatches to the correct extractor based on file_type."""
    if file_type == "txt":
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().strip()
        if not text:
            raise ValueError("This text file appears to be empty.")
        return text

    if file_type in EXTRACTORS:
        return EXTRACTORS[file_type](filepath)

    raise ValueError(f"Text extraction for '{file_type}' files isn't supported.")