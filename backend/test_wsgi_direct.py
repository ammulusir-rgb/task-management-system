"""
Test Django WSGI handler directly, bypassing wsgiref.
"""
import os, sys, io, traceback

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.local"

# Override middleware to absolute minimum before Django setup
print("Setting up Django...")
import django
django.setup()
print("Django setup complete.")

from django.core.handlers.wsgi import WSGIHandler
print("Creating WSGIHandler...")
handler = WSGIHandler()
print("Handler created.")

# Build a minimal WSGI environ for GET /api/schema/
environ = {
    "REQUEST_METHOD": "GET",
    "PATH_INFO": "/api/schema/",
    "SERVER_NAME": "localhost",
    "SERVER_PORT": "8000",
    "HTTP_HOST": "localhost:8000",
    "SERVER_PROTOCOL": "HTTP/1.1",
    "wsgi.input": io.BytesIO(b""),
    "wsgi.errors": sys.stderr,
    "wsgi.url_scheme": "http",
    "wsgi.multithread": False,
    "wsgi.multiprocess": False,
    "wsgi.run_once": False,
    "CONTENT_TYPE": "",
    "CONTENT_LENGTH": "0",
    "QUERY_STRING": "",
}

print("Calling handler with environ...")
response_started = []
def start_response(status, headers, exc_info=None):
    print(f"  start_response called: {status}")
    response_started.append(status)
    return lambda s: None  # write() callable

try:
    result = handler(environ, start_response)
    print(f"Handler returned: {type(result)}")
    body = b"".join(result)
    print(f"Response status: {response_started}")
    print(f"Body length: {len(body)}")
    print(f"Body preview: {body[:200]}")
except Exception as e:
    print(f"Exception: {e}")
    traceback.print_exc()
