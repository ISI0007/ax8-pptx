"""Wire-format proof for every provider in the registry.

Stands up one local server, points each Provider's endpoint at it, and drives
the real llm.complete() path. Verifies per-provider: model field, auth header
presence, JSON boundary extraction, and gate pass.
"""

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from ax8pptx import llm
from ax8pptx.providers import PROVIDERS, Provider, list_providers, resolve

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

SENT = []          # captured request bodies
HEADERS = []       # captured auth headers


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n).decode())
        SENT.append(body)
        HEADERS.append(self.headers.get("Authorization"))
        content = ("Sure, here is your deck:\n\n" + _DECK
                   + "\n\nLet me know if you want changes.")
        payload = json.dumps({"choices": [{"message": {"content": content}}]}).encode()
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
    base = f"http://127.0.0.1:{port}/chat/completions"

    from ax8pptx.intake import Brief
    from ax8pptx.pipeline import deck_from_json, check
    brief = Brief(topic="stub", slide_count=8)

    failures = []
    for src in list_providers():
        prov = Provider(
            id=src.id, name=src.name, endpoint=base, model=src.model,
            key_env=src.key_env, tier=src.tier, needs_key=src.needs_key,
        )
        os.environ[prov.key_env] = "test-key"
        SENT.clear(); HEADERS.clear()
        before = len(failures)
        try:
            raw = llm.complete("draw a deck", provider=prov)
            deck = deck_from_json(raw, brief)
            errs = check(deck, brief)
        except Exception as e:
            failures.append(f"{prov.id}: {type(e).__name__}: {e}")
            continue
        if errs:
            failures.append(f"{prov.id}: gates {errs}")
        if SENT and SENT[-1].get("model") != prov.model:
            failures.append(f"{prov.id}: model not forwarded ({SENT[-1].get('model')!r})")
        if prov.needs_key and not (HEADERS and HEADERS[-1] and HEADERS[-1].startswith("Bearer ")):
            failures.append(f"{prov.id}: missing Bearer auth header")
        if not prov.needs_key and HEADERS and HEADERS[-1]:
            pass  # local servers tolerate an auth header; nothing to assert
        print(f"  {'ok  ' if len(failures) == before else 'FAIL'}{prov.id:<12}{prov.tier:<10}{prov.model}")

    # provider resolution rules: with no keys set, resolve() must not pick a paid provider
    os.environ.pop("AX8_PROVIDER", None)
    for p in list_providers():
        os.environ.pop(p.key_env, None)
    picked = resolve()
    if picked is not None and picked.tier == "paid":
        failures.append(f"resolve() picked a paid provider with no key: {picked.id}")
    if picked is not None and not picked.ready:
        failures.append(f"resolve() returned a not-ready provider: {picked.id}")

    srv.shutdown()
    print(f"\nchecked {len(list_providers())} providers over the real urllib path")
    print("FAILURES:", failures if failures else "none")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
