import google.generativeai as genai
from flask import current_app


def get_gemini_client():
    """Configures and returns a Gemini model instance. Reads the API
    key from app config (not directly from os.environ) so it respects
    Flask's config system — same pattern as every other setting in
    this app, and testable via TestingConfig later if needed."""
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your .env file."
        )
    # Using the "-latest" alias rather than a pinned version (e.g. gemini-2.5-flash)
    # deliberately — pinned model versions get gated to "existing users only" as
    # Google rolls out newer generations, causing 404s on fresh API keys/projects.
    # The alias always resolves to whatever flash-tier model your account currently
    # has access to, avoiding this entire class of breakage.
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-flash-latest")


def generate_content(prompt):
    """The single entry point every service in this app should use to
    talk to Gemini. Centralizing this here means: model choice, retry
    logic, and error handling all live in exactly one place — Phase 5
    (RAG chat) and Phase 6 (Quiz generation) will call this same
    function, not duplicate their own Gemini setup.

    Raises RuntimeError on any failure — callers catch this and turn
    it into a 'failed' status, same pattern as text extraction."""
    model = get_gemini_client()

    try:
        response = model.generate_content(prompt)
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}")

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return response.text