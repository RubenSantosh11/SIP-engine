"""Local preview of the Vercel app: python dev_server.py  (serves public/ and /api/extract on :8000)."""
import http.server
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from api.extract import handler as Api  # noqa: E402


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT / "public"), **k)

    def do_POST(self):  # noqa: N802
        if self.path.startswith("/api/extract"):
            return Api.do_POST(self)
        self.send_error(404)

    _send = Api._send


if __name__ == "__main__":
    os.environ.setdefault("SIP_LLM_PROVIDER", "gemini")
    http.server.ThreadingHTTPServer(("127.0.0.1", int(os.environ.get("PORT", 8000))), H).serve_forever()
