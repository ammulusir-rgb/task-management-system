"""
Local development settings — uses PostgreSQL, in-memory cache.
No Redis/Celery/Daphne required.
Use this for local testing: DJANGO_SETTINGS_MODULE=config.settings.local
"""

from .base import *  # noqa: F401, F403

# ── Debug ──
DEBUG = True

# ── Database — PostgreSQL ──
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "taskmanager",
        "USER": "postgres",
        "PASSWORD": "password",
        "HOST": "127.0.0.1",
        "PORT": "5432",
        "ATOMIC_REQUESTS": True,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# Remove unnecessary packages for local dev (no Redis/Celery/Daphne)
_EXCLUDED_APPS = {
    "storages",
    "daphne",
    "django_celery_beat",
    "channels",
}
INSTALLED_APPS = [  # noqa: F405
    app for app in INSTALLED_APPS  # noqa: F405
    if app not in _EXCLUDED_APPS
]

# ── Cache — local memory (no Redis needed) ──
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "taskmanager-cache",
    }
}

# ── Channels — in-memory layer (no Redis needed) ──
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# ── Celery — eager mode (tasks run synchronously, no broker needed) ──
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ── Additional dev apps ──
try:
    import django_extensions  # noqa: F401
    INSTALLED_APPS += ["django_extensions"]  # noqa: F405
except ImportError:
    pass

# ── CORS — more permissive in dev ──
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

# ── Email — console backend for dev ──
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

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

# ── Logging — simpler for local dev (no file handler) ──
LOGGING = {  # noqa: F405
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}

# ── JWT cookie not secure in dev ──
SIMPLE_JWT_COOKIE_SECURE = False
