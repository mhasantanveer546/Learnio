from app.services.storage_service import upload_file_obj
from app.utils.storage_utils import build_material_key, build_profile_picture_key, build_assignment_attachment_key, generate_object_filename
from app.utils.file_utils import is_allowed_file, get_file_extension, ALLOWED_EXTENSIONS


def _get_file_size(file):
    """Reads size via seek/tell BEFORE any upload happens — boto3's
    upload_fileobj can close the underlying stream once the transfer
    completes, so touching the file object afterward is unreliable."""
    file.seek(0, 2)  # seek to end
    size = file.tell()
    file.seek(0)  # reset to start so upload actually reads from the beginning
    return size


def save_study_material(file, user_id):
    if not is_allowed_file(file.filename):
        raise ValueError("That file type isn't supported. Allowed types: PDF, DOCX, PPTX, TXT, JPG, PNG.")

    ext = get_file_extension(file.filename)
    file_type = ALLOWED_EXTENSIONS[ext]
    filename = generate_object_filename(file.filename)
    storage_key = build_material_key(user_id, filename)

    file_size = _get_file_size(file)
    upload_file_obj(file, storage_key)

    return {"storage_key": storage_key, "file_type": file_type, "file_size": file_size}


def save_profile_picture(file, user_id):
    filename = generate_object_filename(file.filename)
    storage_key = build_profile_picture_key(user_id, filename)
    upload_file_obj(file, storage_key)
    return storage_key


def save_assignment_attachment(file, user_id):
    if not is_allowed_file(file.filename):
        raise ValueError("That file type isn't supported.")

    filename = generate_object_filename(file.filename)
    storage_key = build_assignment_attachment_key(user_id, filename)

    file_size = _get_file_size(file)
    upload_file_obj(file, storage_key)

    return {"storage_key": storage_key, "file_size": file_size}