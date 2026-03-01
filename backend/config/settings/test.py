"""
Test-specific Django settings.
"""

from .base import *  # noqa: F401, F403

# ── Debug ──
DEBUG = False
SECRET_KEY = "test-secret-key-not-for-production"

# ── Faster password hashing for tests ──
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# ── Use in-memory channel layer for tests ──
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# ── Use local memory cache for tests ──
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ── Celery — eager execution for tests ──
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ── Email — in-memory backend ──
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ── Disable throttling in tests ──
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}  # noqa: F405

# ── Media — temp dir for tests ──
import tempfile

MEDIA_ROOT = tempfile.mkdtemp()
