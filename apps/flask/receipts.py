import uuid
from pathlib import Path

from config import UPLOADS_DIR

ALLOWED_RECEIPT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_RECEIPT_SIZE_BYTES = 10 * 1024 * 1024


def validate_receipt_upload(file_storage, content_length):
    if file_storage is None or not file_storage.filename:
        return None, "A receipt image file is required."

    extension = Path(file_storage.filename).suffix.lower()

    if extension not in ALLOWED_RECEIPT_EXTENSIONS:
        return None, "Receipt must be a JPG, PNG, or WEBP image."

    if content_length and content_length > MAX_RECEIPT_SIZE_BYTES:
        return None, "Receipt image must be 10MB or smaller."

    return extension, None


def save_receipt_file(purchase_id, file_storage, extension):
    filename = f"{purchase_id}-{uuid.uuid4().hex}{extension}"
    file_storage.save(UPLOADS_DIR / filename)
    return filename


def delete_receipt_file(filename):
    if not filename:
        return

    try:
        (UPLOADS_DIR / filename).unlink()
    except FileNotFoundError:
        pass
