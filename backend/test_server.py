"""Minimal test server to verify wsgiref works."""
from wsgiref.simple_server import make_server

def simple_app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b'Hello World\n']

if __name__ == '__main__':
    httpd = make_server('0.0.0.0', 8001, simple_app)
    print('Test server on http://localhost:8001/', flush=True)
    httpd.serve_forever()
