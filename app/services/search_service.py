from app.models import Subject, StudyMaterial, Summary, Flashcard, FlashcardSet, Assignment, Exam
from sqlalchemy.orm import joinedload

def global_search(user_id, query, limit_per_type=10):
    """Searches across everything a user owns: Subjects, Materials,
    Summaries, Flashcards, Assignments, Exams. Plain SQL LIKE search —
    deliberately not FAISS-based, since Phase 5's per-material index
    design means there's no single shared vector index to search
    against; querying every material's separate index per keystroke
    would be slow and pointless for simple keyword lookup.

    Returns a dict grouped by type, each entry carrying enough info
    to link back to the real page."""
    like_query = f"%{query}%"
    results = {}

    subjects = (
        Subject.query.filter(Subject.user_id == user_id, Subject.name.ilike(like_query))
        .limit(limit_per_type).all()
    )
    results["subjects"] = [
        {"title": s.name, "url_kwargs": {"subject_id": s.id}} for s in subjects
    ]

    materials = (
        StudyMaterial.query.filter(
            StudyMaterial.user_id == user_id,
            db_or(StudyMaterial.original_name.ilike(like_query), StudyMaterial.extracted_text.ilike(like_query)),
        )
        .options(joinedload(StudyMaterial.subject))
        .limit(limit_per_type).all()
    )
    results["materials"] = [
        {"title": m.original_name, "subtitle": m.subject.name, "url_kwargs": {"subject_id": m.subject_id}}
        for m in materials
    ]

    summaries = (
        Summary.query.join(StudyMaterial)
        .filter(StudyMaterial.user_id == user_id, Summary.content.ilike(like_query))
        .options(joinedload(Summary.material))
        .limit(limit_per_type).all()
    )
    results["summaries"] = [
        {"title": s.material.original_name, "subtitle": "Summary", "url_kwargs": {"material_id": s.material_id}}
        for s in summaries
    ]

    flashcards = (
        Flashcard.query.join(FlashcardSet).join(StudyMaterial)
        .filter(
            StudyMaterial.user_id == user_id,
            db_or(Flashcard.front_text.ilike(like_query), Flashcard.back_text.ilike(like_query)),
        )
        .options(joinedload(Flashcard.flashcard_set).joinedload(FlashcardSet.material))
        .limit(limit_per_type).all()
    )
    results["flashcards"] = [
        {
            "title": f.front_text[:80],
            "subtitle": f.flashcard_set.material.original_name,
            "url_kwargs": {"material_id": f.flashcard_set.material_id},
        }
        for f in flashcards
    ]

    assignments = (
        Assignment.query.filter(
            Assignment.user_id == user_id,
            db_or(Assignment.title.ilike(like_query), Assignment.description.ilike(like_query)),
        )
        .options(joinedload(Assignment.subject))
        .limit(limit_per_type).all()
    )
    results["assignments"] = [
        {"title": a.title, "subtitle": a.subject.name, "url_kwargs": {}} for a in assignments
    ]

    exams = (
        Exam.query.filter(
            Exam.user_id == user_id,
            db_or(Exam.title.ilike(like_query), Exam.notes.ilike(like_query), Exam.location.ilike(like_query)),
        )
        .options(joinedload(Exam.subject))
        .limit(limit_per_type).all()
    )
    results["exams"] = [
        {"title": e.title, "subtitle": e.subject.name, "url_kwargs": {}} for e in exams
    ]

    return results


def db_or(*clauses):
    from app.extensions import db
    return db.or_(*clauses)