"""Validation helpers for ticket/comment image uploads."""

from pathlib import Path

from django.conf import settings
from rest_framework.exceptions import ValidationError


ALLOWED_EXTENSIONS = getattr(
    settings, "TICKET_IMAGE_EXTENSIONS", {".jpg", ".jpeg", ".png", ".gif", ".webp"}
)
MAX_BYTES = getattr(settings, "TICKET_IMAGE_MAX_BYTES", 5 * 1024 * 1024)
MAX_FILES = getattr(settings, "TICKET_IMAGE_MAX_FILES", 5)


def validate_image_file(uploaded_file):
    name = getattr(uploaded_file, "name", "") or ""
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )
    size = getattr(uploaded_file, "size", None)
    if size is not None and size > MAX_BYTES:
        raise ValidationError(f"Image exceeds max size of {MAX_BYTES // (1024 * 1024)} MB.")
    return uploaded_file


def collect_upload_files(request):
    """Pull image files from multipart request (file, files, files[])."""
    files = []
    if request.FILES.get("file"):
        files.append(request.FILES["file"])
    files.extend(request.FILES.getlist("files"))
    files.extend(request.FILES.getlist("files[]"))
    # de-dupe by identity while preserving order
    seen = set()
    unique = []
    for f in files:
        key = id(f)
        if key not in seen:
            seen.add(key)
            unique.append(f)
    if len(unique) > MAX_FILES:
        raise ValidationError(f"At most {MAX_FILES} images allowed.")
    for f in unique:
        validate_image_file(f)
    return unique
