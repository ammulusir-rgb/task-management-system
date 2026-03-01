import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.local"

import logging
logging.disable(logging.CRITICAL)

import django
django.setup()
print("Django setup OK", flush=True)

from django.core.management import call_command

print("Running makemigrations...", flush=True)
call_command("makemigrations", verbosity=1)
print("makemigrations done", flush=True)

print("Running migrate...", flush=True)
call_command("migrate", verbosity=1)
print("migrate done", flush=True)

print("Creating superuser...", flush=True)
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email="admin@example.com").exists():
    User.objects.create_superuser(
        email="admin@example.com",
        password="admin123456",
        first_name="Admin",
        last_name="User",
    )
    print("Superuser created: admin@example.com / admin123456", flush=True)
else:
    print("Superuser already exists", flush=True)

print("ALL DONE", flush=True)
