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