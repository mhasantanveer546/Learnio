import boto3
from botocore.client import Config
from flask import current_app, g


def get_r2_client():
    if "r2_client" not in g:
        g.r2_client = boto3.client(
            "s3",
            endpoint_url=current_app.config["R2_ENDPOINT_URL"],
            aws_access_key_id=current_app.config["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=current_app.config["R2_SECRET_ACCESS_KEY"],
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
    return g.r2_client

def upload_file_obj(file_obj, storage_key):
    """Uploads a file-like object directly to R2 — no local disk
    involved. file_obj can be a Werkzeug FileStorage (from a form
    upload) or any file-like object with .read()."""
    client = get_r2_client()
    bucket = current_app.config["R2_BUCKET_NAME"]
    client.upload_fileobj(file_obj, bucket, storage_key)


def generate_download_url(storage_key, filename, expires_in=300):
    """Generates a short-lived signed URL for direct browser download.
    Only ever call this AFTER an ownership check — the URL itself
    grants access to anyone who has it for its lifetime."""
    client = get_r2_client()
    bucket = current_app.config["R2_BUCKET_NAME"]

    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": bucket,
            "Key": storage_key,
            "ResponseContentDisposition": f'attachment; filename="{filename}"',
        },
        ExpiresIn=expires_in,
    )


def download_to_temp(storage_key, suffix=""):
    """Downloads an R2 object to a local temp file for processing
    (text extraction, OCR) — scratch space only, not permanent
    storage. Caller is responsible for deleting it afterward."""
    import tempfile

    client = get_r2_client()
    bucket = current_app.config["R2_BUCKET_NAME"]

    fd, temp_path = tempfile.mkstemp(suffix=suffix)
    import os
    os.close(fd)

    client.download_file(bucket, storage_key, temp_path)
    return temp_path


def delete_file(storage_key):
    client = get_r2_client()
    bucket = current_app.config["R2_BUCKET_NAME"]
    client.delete_object(Bucket=bucket, Key=storage_key)