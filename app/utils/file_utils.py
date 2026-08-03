import os
import uuid
from werkzeug.utils import secure_filename


def save_profile_picture(file, user_id, upload_folder):
    """Saves an uploaded profile picture to uploads/users/user_<id>/profile/
    and returns the filename to store in User.profile_picture.

    Uses a random UUID filename (not the original name) to avoid:
    - filename collisions between users
    - path traversal via a maliciously crafted filename
    - leaking the original filename/extension info unnecessarily
    """
    ext = os.path.splitext(secure_filename(file.filename))[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"

    user_dir = os.path.join(upload_folder, "users", f"user_{user_id}", "profile")
    os.makedirs(user_dir, exist_ok=True)

    file.save(os.path.join(user_dir, filename))
    return filename