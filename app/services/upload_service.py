import os
import uuid

from app.utils.file_utils import ALLOWED_EXTENSIONS, get_file_extension, is_allowed_file


def save_profile_picture(file, user_id, upload_folder):
    """Saves an uploaded profile picture to uploads/users/user_<id>/profile/
    and returns the filename to store in User.profile_picture.

    Uses a random UUID filename (not the original name) to avoid:
    - filename collisions between users
    - path traversal via a maliciously crafted filename
    - leaking the original filename/extension info unnecessarily
    """
    ext = get_file_extension(file.filename) or ""
    filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

    user_dir = os.path.join(upload_folder, "users", f"user_{user_id}", "profile")
    os.makedirs(user_dir, exist_ok=True)

    file.save(os.path.join(user_dir, filename))
    return filename


def save_study_material(file, user_id, upload_folder):
    """Validates and saves an uploaded study material.

    Returns a dict: {"filename", "file_type", "file_size"}.
    Raises ValueError if the file type isn't allowed — the route is
    responsible for catching this and flashing a user-facing message.
    """
    if not is_allowed_file(file.filename):
        raise ValueError(
            "That file type isn't supported. Allowed types: PDF, DOCX, PPTX, TXT, JPG, PNG."
        )

    ext = get_file_extension(file.filename)
    file_type = ALLOWED_EXTENSIONS[ext]
    filename = f"{uuid.uuid4().hex}.{ext}"

    user_dir = os.path.join(upload_folder, "users", f"user_{user_id}", "notes")
    os.makedirs(user_dir, exist_ok=True)

    filepath = os.path.join(user_dir, filename)
    file.save(filepath)
    file_size = os.path.getsize(filepath)

    return {"filename": filename, "file_type": file_type, "file_size": file_size}