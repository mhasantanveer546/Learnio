def build_summary_prompt(extracted_text):
    """Builds the prompt for generating a full structured study summary
    from a material's extracted text. Asks for one Markdown document
    with four fixed sections, so downstream rendering (summary.html)
    can rely on consistent structure."""

    # Gemini has a context window, but extremely long lecture PDFs could
    # still be excessive — truncate defensively rather than let one giant
    # document silently blow the budget or produce a degraded response.
    max_chars = 30000
    text = extracted_text[:max_chars]

    return f"""You are an expert study assistant helping a university student understand their lecture material.

Given the following extracted text from a student's study material, produce a single well-structured Markdown document with EXACTLY these four sections, in this order, using these exact headers:

# Chapter Summary
A clear, concise summary of the main content (3-6 paragraphs).

# Key Concepts
A bulleted list of the most important concepts, each with a one-line explanation.

# Important Definitions
A bulleted list of key terms and their definitions, formatted as **Term**: definition.

# Formula Sheet
A bulleted list of any formulas, equations, or key facts present in the material. If none exist, write "No formulas found in this material."

Do not add any text before the first header or after the last section. Do not include commentary about these instructions.

STUDY MATERIAL TEXT:
{text}
"""