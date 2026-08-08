import os

ALLOWED_EXTENSIONS = {
    "pdf": "pdf",
    "docx": "docx",
    "pptx": "pptx",
    "txt": "txt",
    "jpg": "jpg",
    "jpeg": "jpg",
    "png": "png",
}


def get_file_extension(filename):
    if not filename or "." not in filename:
        return None
    return filename.rsplit(".", 1)[1].lower()


def is_allowed_file(filename):
    ext = get_file_extension(filename)
    return ext in ALLOWED_EXTENSIONS

def get_material_filepath(upload_folder, user_id, filename):
    """Reconstructs the full disk path for a study material.
    Single source of truth for this path — used by upload, delete,
    process, and download, so the folder structure only ever needs
    to change in one place."""
    return os.path.join(upload_folder, "users", f"user_{user_id}", "notes", filename)


def get_profile_picture_filepath(upload_folder, user_id, filename):
    """Same idea, for profile pictures."""
    return os.path.join(upload_folder, "users", f"user_{user_id}", "profile", filename)


def get_assignment_attachment_filepath(upload_folder, user_id, filename):
    return os.path.join(upload_folder, "users", f"user_{user_id}", "assignments", filename)