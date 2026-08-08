from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from app.services.search_service import global_search

search_bp = Blueprint("search", __name__, url_prefix="/search")


@search_bp.route("/", methods=["GET"])
@login_required
def search_results():
    query = request.args.get("q", "").strip()

    if not query:
        return render_template("search/results.html", query="", results=None)

    results = global_search(current_user.id, query)
    return render_template("search/results.html", query=query, results=results)


@search_bp.route("/live", methods=["GET"])
@login_required
def search_live():
    """JSON endpoint for the topnav's live-search dropdown — returns a
    small, capped result set for a fast preview, not the full page."""
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify({})

    results = global_search(current_user.id, query, limit_per_type=3)
    return jsonify(results)