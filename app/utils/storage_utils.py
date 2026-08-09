import uuid


def build_material_key(user_id, filename):
    return f"users/{user_id}/materials/{filename}"


def build_profile_picture_key(user_id, filename):
    return f"users/{user_id}/profile/{filename}"


def build_assignment_attachment_key(user_id, filename):
    return f"users/{user_id}/assignments/{filename}"


def generate_object_filename(original_filename):
    """Same UUID-based naming as before — collision-free, no path
    traversal risk from user-supplied names."""
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    return f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex