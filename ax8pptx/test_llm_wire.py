"""Offline proof that llm.complete() works without the real API.

Spins a local HTTP server that speaks the OpenAI/DeepSeek chat-completions
wire format, points the client at it, and asserts parsing + gate pass.
This exercises the real urllib code path, not a mock of it.
"""

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from ax8pptx import llm

_SLIDES = [
    {"layout": "cover", "title": "Stub", "subtitle": "proves the wire format"},
    {"layout": "section", "title": "Part one", "subtitle": "01"},
    {"layout": "bullets", "title": "Path",
     "bullets": ["real urllib", "real json parse", "real gates"]},
    {"layout": "two_col", "title": "Layers", "left_title": "Spec",
     "left_bullets": ["slots"], "right_title": "Render", "right_bullets": ["tokens"]},
    {"layout": "kpi_row", "title": "Numbers",
     "kpis": [{"value": "8", "label": "slides"}, {"value": "0", "label": "errors"}]},
    {"layout": "quote", "quote": "The model never draws.", "attribution": "rule"},
    {"layout": "bullets", "title": "Rest", "bullets": ["ship it"]},
    {"layout": "closing", "title": "Done", "subtitle": "stub server"},
]
_DECK = json.dumps({"title": "Stub", "subtitle": "wire test", "slides": _SLIDES})

RESPONSE = {
    "choices": [{
        "message": {
        "content": 'Sure, here is your deck:\n\n' + _DECK + '\n\nLet me know if you want changes.'
        }
    }]
}


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n).decode())
        assert body["model"], "model missing"
        assert body["messages"], "messages missing"
        assert self.headers["Authorization"].startswith("Bearer test-"), "auth header missing"
        payload = json.dumps(RESPONSE).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *a):
        pass


def main() -> int:
    srv = HTTPServer(("127.0.0.1", 0), H)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    os.environ["DEEPSEEK_API_KEY"] = "test-key"
    llm.ENDPOINT = f"http://127.0.0.1:{port}/chat/completions"

    from ax8pptx.intake import Brief
    from ax8pptx.pipeline import deck_from_json, check

    raw = llm.complete("draw a deck")
    brief = Brief(topic="stub", slide_count=8)
    deck = deck_from_json(raw, brief)
    errs = check(deck, brief)
    print("round-trip OK:", len(deck.slides), "slides, gates:", errs or "clean")
    srv.shutdown()
    return 0 if not errs else 1
