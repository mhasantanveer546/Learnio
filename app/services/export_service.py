import csv
import io
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def _pdf_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="LearnioTitle", fontSize=18, spaceAfter=6, textColor=colors.HexColor("#2563EB")))
    styles.add(ParagraphStyle(name="LearnioMeta", fontSize=10, textColor=colors.HexColor("#64748B"), spaceAfter=16))
    styles.add(ParagraphStyle(name="LearnioHeading", fontSize=13, spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#1E293B")))
    styles.add(ParagraphStyle(name="LearnioBody", fontSize=10.5, leading=15))
    return styles


def export_summary_pdf(material, summary):
    """Builds a PDF from a Summary's Markdown content. Returns a
    BytesIO buffer — never touches disk, since Vercel's serverless
    filesystem is read-only outside /tmp and nothing persists between
    requests anyway."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = _pdf_styles()
    story = []

    story.append(Paragraph(material.original_name, styles["LearnioTitle"]))
    story.append(Paragraph(f"Generated {datetime.now().strftime('%B %d, %Y')} &middot; {material.subject.name}", styles["LearnioMeta"]))

    # Minimal Markdown-to-PDF: split on our known "# Section" headers
    # (the exact structure build_summary_prompt asks Gemini for),
    # render each as a heading + body paragraphs. Not a general
    # Markdown parser — deliberately narrow, matching the one format
    # we actually generate.
    for block in summary.content.split("\n# "):
        block = block.strip()
        if not block:
            continue
        lines = block.lstrip("#").strip().split("\n", 1)
        heading = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""

        story.append(Paragraph(heading, styles["LearnioHeading"]))
        for para in body.split("\n"):
            para = para.strip().lstrip("-").strip()
            if para:
                story.append(Paragraph(para, styles["LearnioBody"]))
                story.append(Spacer(1, 4))

    doc.build(story)
    buffer.seek(0)
    return buffer


def export_flashcards_csv(flashcard_set):
    """Returns a StringIO buffer of Front,Back,Difficulty rows —
    directly importable into Anki/Quizlet, which is the whole point
    of choosing CSV here over a Learnio-specific format."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Front", "Back", "Difficulty"])

    for card in flashcard_set.cards:
        writer.writerow([card.front_text, card.back_text, card.difficulty])

    buffer.seek(0)
    return io.BytesIO(buffer.getvalue().encode("utf-8"))


def export_quiz_history_csv(material, attempts):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Score", "Total", "Percentage"])

    for a in attempts:
        pct = round((a.score / a.total) * 100) if a.total else 0
        writer.writerow([a.started_at.strftime("%Y-%m-%d %H:%M"), a.score, a.total, f"{pct}%"])

    buffer.seek(0)
    return io.BytesIO(buffer.getvalue().encode("utf-8"))


def export_quiz_review_pdf(attempt):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = _pdf_styles()
    story = []

    pct = round((attempt.score / attempt.total) * 100) if attempt.total else 0
    story.append(Paragraph(attempt.quiz.title, styles["LearnioTitle"]))
    story.append(Paragraph(f"Score: {attempt.score}/{attempt.total} ({pct}%)", styles["LearnioMeta"]))

    for i, answer in enumerate(attempt.answers, start=1):
        story.append(Paragraph(f"Question {i}", styles["LearnioHeading"]))
        story.append(Paragraph(answer.question.question_text, styles["LearnioBody"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Your answer:</b> {answer.submitted_answer or '(no answer)'}", styles["LearnioBody"]))
        story.append(Paragraph(f"<b>Correct/suggested answer:</b> {answer.question.correct_answer}", styles["LearnioBody"]))

        if answer.is_correct is True:
            story.append(Paragraph("Correct", ParagraphStyle(name="ok", textColor=colors.HexColor("#10B981"), fontSize=10, spaceBefore=2)))
        elif answer.is_correct is False:
            story.append(Paragraph("Incorrect", ParagraphStyle(name="bad", textColor=colors.HexColor("#EF4444"), fontSize=10, spaceBefore=2)))
        story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer