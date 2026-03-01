"""
Utility functions for the Task Management SaaS.
"""

import os
import re
import uuid
from datetime import datetime

from django.conf import settings
from django.utils.text import slugify


def generate_unique_slug(text: str, max_length: int = 50) -> str:
    """Generate a unique slug by appending a short UUID suffix."""
    base_slug = slugify(text)[:max_length - 9]  # Reserve space for UUID suffix
    unique_suffix = uuid.uuid4().hex[:8]
    return f"{base_slug}-{unique_suffix}"


def file_upload_path(instance, filename: str) -> str:
    """
    Generate a structured upload path based on model and date.
    E.g., uploads/tasks/2026/02/28/<uuid>_filename.ext
    """
    model_name = instance.__class__.__name__.lower()
    now = datetime.now()
    ext = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return f"uploads/{model_name}/{now.year}/{now.month:02d}/{now.day:02d}/{unique_name}"


def validate_file_extension(filename: str) -> bool:
    """Check if a file extension is in the allowed list."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in settings.ALLOWED_UPLOAD_EXTENSIONS


def validate_file_size(file) -> bool:
    """Check if a file size is within the allowed limit."""
    return file.size <= settings.MAX_UPLOAD_SIZE


def sanitize_html(html_content: str) -> str:
    """
    Basic HTML sanitization — strip dangerous tags.
    For production, consider using bleach or similar.
    """
    dangerous_tags = re.compile(
        r"<\s*(script|iframe|object|embed|form|input|textarea|select|button)[^>]*>.*?<\s*/\s*\1\s*>",
        re.IGNORECASE | re.DOTALL,
    )
    return dangerous_tags.sub("", html_content)


def get_client_ip(request) -> str:
    """Extract client IP from request, handling proxies."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")
