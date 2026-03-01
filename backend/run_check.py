import os
import sys
import traceback

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.local"

try:
    import django
    django.setup()
    print("Django setup successful", flush=True)
    
    from django.core.management import call_command
    call_command("check", verbosity=2)
    print("Django check passed!", flush=True)
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)
