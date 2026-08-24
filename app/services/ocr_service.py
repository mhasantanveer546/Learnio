"""Image text extraction using OCR.space API.
Falls back gracefully if no API key is configured."""

import requests
from flask import current_app


def extract_text_from_image(filepath):
    """Extract text from an image (jpg/png) using OCR.space API.
    Raises ValueError if no text is found or if the API key is missing."""
    api_key = current_app.config.get("OCR_SPACE_API_KEY")

    if not api_key:
        raise ValueError(
            "Image text extraction requires an OCR_SPACE_API_KEY. "
            "Get a free key at https://ocr.space/ocrapi/free and add it "
            "to your environment variables. Alternatively, upload PDF, "
            "DOCX, PPTX, or TXT files instead."
        )

    with open(filepath, "rb") as f:
        response = requests.post(
            "https://api.ocr.space/parse/image",
            files={"image": f},
            data={
                "apikey": api_key,
                "language": "eng",
                "isOverlayRequired": False,
                "filetype": "Auto",
            },
            timeout=30,
        )

    response.raise_for_status()
    result = response.json()

    if result.get("IsErroredOnProcessing"):
        error_msg = result.get("ErrorMessage", ["Unknown error"])[0]
        raise ValueError(f"OCR failed: {error_msg}")

    parsed_results = result.get("ParsedResults", [])
    if not parsed_results:
        raise ValueError(
            "No readable text found in this image. It may be blank, "
            "too low quality, or contain no text."
        )

    text = parsed_results[0].get("ParsedText", "").strip()

    if not text:
        raise ValueError(
            "No readable text found in this image. It may be blank, "
            "too low quality, or contain no text."
        )

    return text