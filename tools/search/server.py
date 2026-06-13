"""Tiny stdlib HTTP server with a search UI. Uses no external web framework."""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import html

from tools.search.index import load_index
from tools.search.query import query as run_query


PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Wiki Search</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 2em auto; padding: 0 1em; }}
input[type=text] {{ width: 70%; padding: 0.5em; font-size: 1em; }}
li {{ margin: 0.4em 0; }}
.type {{ color: #888; font-size: 0.85em; margin-right: 0.5em; }}
</style></head><body>
<h1>Wiki Search</h1>
<form><input type="text" name="q" value="{q}" autofocus> <input type="submit" value="Search"></form>
{results}
</body></html>
"""


def make_handler(idx):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a, **kw):
            pass  # silence

        def do_GET(self):
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            q = (qs.get("q") or [""])[0]
            if q.strip():
                hits = run_query(idx, q, limit=50)
                if hits:
                    items = "".join(
                        f'<li><span class="type">[{html.escape(h.type)}]</span>'
                        f'<strong>{html.escape(h.title)}</strong> '
                        f'<code>{html.escape(h.path)}</code></li>'
                        for h in hits
                    )
                    results = f"<ul>{items}</ul>"
                else:
                    results = "<p>(no results)</p>"
            else:
                results = ""
            body = PAGE.format(q=html.escape(q), results=results).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return H


def serve(index_path: str, port: int) -> None:
    idx = load_index(index_path)
    server = HTTPServer(("127.0.0.1", port), make_handler(idx))
    print(f"serving search UI on http://127.0.0.1:{port}  (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
