import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.local"

# Disable file logging to avoid blocks
import logging
logging.disable(logging.CRITICAL)

import django
django.setup()
print("Django setup OK", flush=True)

from django.core import checks
errors = checks.run_checks()
if errors:
    for e in errors:
        print(f"  {e}", flush=True)
else:
    print("System check: no issues found.", flush=True)

print("SCRIPT_DONE", flush=True)
