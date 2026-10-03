#!/usr/bin/env python3
"""Static preview server that mirrors the Netlify routing rules.

Netlify serves real files first, then /product/* as product pages, then falls
back to index.html. Plain http.server would 404 on those paths, so the preview
would not match production. Usage: python3 tools/preview_server.py [port]
"""
import http.server
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def translate_path(self, path):
        local = super().translate_path(path)
        if os.path.exists(local) and os.path.isfile(local):
            return local
        if path.startswith("/product/"):
            page = os.path.join(ROOT, "product", "index.html")
            if os.path.isfile(page):
                return page
        return os.path.join(ROOT, "index.html")

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 12000
    http.server.ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
