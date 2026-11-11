"""
services/storage_service.py
-----------------------------
Small storage abstraction so the rest of the app doesn't care whether
uploaded files land on local disk (default, great for demos) or in an
S3-compatible bucket (set STORAGE_BACKEND=s3 in .env).
"""

import logging
import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)


def _unique_filename(original_filename: str) -> str:
    safe_name = secure_filename(original_filename) or "document.pdf"
    return f"{uuid.uuid4().hex}_{safe_name}"


def save_file(file_storage) -> tuple[str, str]:
    """
    Persist an uploaded file (Werkzeug FileStorage).

    Returns (stored_filename, storage_path) where storage_path is either
    a local filesystem path or an S3 URI, depending on STORAGE_BACKEND.
    """
    backend = current_app.config["STORAGE_BACKEND"]
    stored_name = _unique_filename(file_storage.filename)

    if backend == "s3":
        return _save_to_s3(file_storage, stored_name)
    return _save_locally(file_storage, stored_name)


def _save_locally(file_storage, stored_name: str) -> tuple[str, str]:
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    path = os.path.join(upload_folder, stored_name)
    file_storage.save(path)
    return stored_name, path


def _save_to_s3(file_storage, stored_name: str) -> tuple[str, str]:  # pragma: no cover
    """Upload to S3. Requires boto3 + valid credentials in .env."""
    import boto3

    bucket = current_app.config["S3_BUCKET_NAME"]
    region = current_app.config["S3_REGION"]

    s3 = boto3.client(
        "s3",
        region_name=region,
        aws_access_key_id=current_app.config["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
    )
    s3.upload_fileobj(file_storage, bucket, stored_name)
    uri = f"s3://{bucket}/{stored_name}"
    return stored_name, uri


def get_local_path(storage_path: str) -> str:
    """
    For processing (OCR), we need a real local filesystem path. If the
    backend is S3 this would download to a temp file first; for the local
    backend the storage_path already *is* the local path.
    """
    backend = current_app.config["STORAGE_BACKEND"]
    if backend == "local":
        return storage_path

    import tempfile

    import boto3

    bucket = current_app.config["S3_BUCKET_NAME"]
    key = storage_path.replace(f"s3://{bucket}/", "")
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    s3 = boto3.client("s3", region_name=current_app.config["S3_REGION"])
    s3.download_fileobj(bucket, key, tmp)
    tmp.close()
    return tmp.name
