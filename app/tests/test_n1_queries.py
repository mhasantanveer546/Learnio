"""N+1 query detection tests."""

from sqlalchemy import event
from app.extensions import db
from app.models import Subject


def _count_queries():
    counter = [0]

    def listener(conn, cursor, statement, parameters, context, executemany):
        counter[0] += 1

    event.listen(db.engine, "before_cursor_execute", listener)
    return counter, listener


def _stop_counting(listener):
    event.remove(db.engine, "before_cursor_execute", listener)


def test_subject_detail_no_n1(client, make_user, make_material, login_client):
    """Viewing a subject with materials should not trigger N+1 queries."""
    owner = make_user()
    materials = [make_material(owner=owner, status="ready") for _ in range(5)]
    subject = materials[0].subject

    counter, listener = _count_queries()
    try:
        login_client(owner)
        response = client.get(f"/subjects/{subject.id}")
    finally:
        _stop_counting(listener)

    assert response.status_code == 200
    assert counter[0] <= 6, f"N+1 detected: {counter[0]} queries"


def test_dashboard_no_n1(client, make_user, make_material, login_client):
    """Dashboard should not trigger N+1."""
    owner = make_user()
    for _ in range(3):
        make_material(owner=owner, status="ready")

    counter, listener = _count_queries()
    try:
        login_client(owner)
        response = client.get("/dashboard")
    finally:
        _stop_counting(listener)

    assert response.status_code == 200
    assert counter[0] <= 12, f"N+1 detected: {counter[0]} queries"