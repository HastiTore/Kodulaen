#!/usr/bin/env python3
"""Serve dist/ at http://127.0.0.1:8765/Kodulaen/ for a local check of the Pages base path."""
import http.server
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "dist"
PORT = int(os.environ.get("PORT", "8765"))
PREFIX = os.environ.get("BASE_PATH", "/Kodulaen").rstrip("/")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def translate_path(self, path):
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if clean == PREFIX:
            clean = PREFIX + "/"
        if clean == PREFIX + "/" or clean.startswith(PREFIX + "/"):
            clean = clean[len(PREFIX):] or "/"
        else:
            clean = "/__missing__"
        return super().translate_path(clean)


def main():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Serving {ROOT} at http://127.0.0.1:{PORT}{PREFIX}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
