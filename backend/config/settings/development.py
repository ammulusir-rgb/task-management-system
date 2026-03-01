"""
Development-specific Django settings.
"""

from .base import *  # noqa: F401, F403

# ── Debug ──
DEBUG = True

# ── Additional dev apps ──
INSTALLED_APPS += [  # noqa: F405
    "django_extensions",
]

# ── CORS — more permissive in dev ──
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://localhost:80",
    "http://127.0.0.1:80",
]

# ── Email — console backend for dev ──
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ── Cache — use Redis in dev too, but with shorter TTLs ──
CACHES["default"]["TIMEOUT"] = 60  # noqa: F405

# ── Static Files ──
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ── REST Framework — add browsable API in dev ──
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

# ── Logging — more verbose in dev ──
LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # noqa: F405

# ── JWT cookie not secure in dev ──
SIMPLE_JWT_COOKIE_SECURE = False
