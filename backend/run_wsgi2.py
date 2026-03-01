"""Test WSGI server with Django but minimal middleware."""
import os
import sys
from wsgiref.simple_server import make_server

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.local"

# Override middleware before setup
import django
from django.conf import settings

# Minimal middleware - override before full setup
import config.settings.local as local_settings
local_settings.MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

django.setup()
print("Django setup complete", flush=True)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
print("WSGI app loaded", flush=True)

httpd = make_server("0.0.0.0", 8000, application)
print("Server running at http://localhost:8000/", flush=True)
httpd.serve_forever()
