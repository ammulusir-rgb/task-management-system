"""
Celery app auto-loading for Task Management SaaS.
This ensures Celery tasks are discovered when Django starts.
"""
import os

_settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")

# Skip Celery import for local settings (no broker), or when Celery is unavailable
if "local" not in _settings_module:
    try:
        from .celery import app as celery_app

        __all__ = ("celery_app",)
    except Exception:  # pragma: no cover
        celery_app = None
        __all__ = ()
else:
    celery_app = None
    __all__ = ()
