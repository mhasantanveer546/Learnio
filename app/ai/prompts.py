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

def build_quiz_prompt(extracted_text, num_questions, question_types, difficulty):
    """Builds a prompt requesting a specific mix of question types and
    count, asking Gemini to return structured JSON (not Markdown, since
    this needs to be reliably parsed into QuizQuestion rows — unlike
    the summary, which is meant to be read as-is)."""

    max_chars = 30000
    text = extracted_text[:max_chars]

    type_labels = {
        "mcq": "multiple choice (4 options, one correct)",
        "true_false": "true/false",
        "short": "short answer (a few sentences)",
        "long": "long answer (a paragraph or more)",
    }
    requested_types = ", ".join(type_labels[t] for t in question_types)

    return f"""You are creating a quiz for a university student based on their study material.

Generate EXACTLY {num_questions} questions at {difficulty} difficulty, using ONLY these question types: {requested_types}. Distribute the questions roughly evenly across the requested types.

Return ONLY valid JSON (no markdown formatting, no code fences, no commentary) matching this exact structure:

{{
  "questions": [
    {{
      "type": "mcq",
      "question": "question text",
      "options": ["A) option one", "B) option two", "C) option three", "D) option four"],
      "correct_answer": "A"
    }},
    {{
      "type": "true_false",
      "question": "question text",
      "options": null,
      "correct_answer": "true"
    }},
    {{
      "type": "short",
      "question": "question text",
      "options": null,
      "correct_answer": "a suggested model answer for self-comparison"
    }}
  ]
}}

Rules:
- "type" must be exactly one of: mcq, true_false, short, long
- For mcq: "options" is an array of 4 strings prefixed with A)/B)/C)/D), "correct_answer" is just the letter (e.g. "B")
- For true_false: "options" is null, "correct_answer" is exactly "true" or "false"
- For short/long: "options" is null, "correct_answer" is a model answer the student can compare their own answer against
- All questions must be answerable from the material below — do not invent facts not present in the text.

STUDY MATERIAL:
{text}
"""