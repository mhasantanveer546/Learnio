from PIL import Image
import pytesseract
from pytesseract.pytesseract import TesseractNotFoundError
from flask import current_app


def _configure_tesseract():
    """If TESSERACT_CMD is set (e.g. installed to a non-default drive/
    folder, not on system PATH), point pytesseract at it explicitly.
    If not set, pytesseract falls back to searching PATH itself."""
    tesseract_cmd = current_app.config.get("TESSERACT_CMD")
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


def extract_text_from_image(filepath):
    """Runs OCR on an image file (jpg/png) and returns extracted text.
    Raises ValueError if no readable text is found or if Tesseract is
    not available — same contract as the other extractors so the
    dispatcher in text_extraction_service.py can handle all formats
    uniformly."""
    _configure_tesseract()

    try:
        image = Image.open(filepath)
    except Exception as e:
        raise ValueError(f"Could not open image file: {e}")

    # Grayscale conversion — a simple, cheap preprocessing step that
    # measurably helps Tesseract's accuracy on photographed/scanned
    # notes, which often have uneven lighting or color noise that
    # doesn't carry any useful information for text recognition.
    image = image.convert("L")

    try:
        text = pytesseract.image_to_string(image).strip()
    except (TesseractNotFoundError, FileNotFoundError) as e:
        # Tesseract is not installed or not on PATH. On serverless
        # environments like Vercel, system binaries like Tesseract are
        # typically not available. Convert to ValueError so the caller
        # can mark the material as failed instead of crashing with 500.
        raise ValueError(
            "Image text extraction (OCR) is not available in this environment. "
            "Tesseract is not installed or not found in PATH. "
            "Please upload PDF, DOCX, PPTX, or TXT files instead."
        ) from e

    if not text:
        raise ValueError(
            "No readable text found in this image. It may be blank, "
            "too low quality, or contain no text."
        )

    return text