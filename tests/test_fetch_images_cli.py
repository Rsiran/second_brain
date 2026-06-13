import subprocess
import sys
from pathlib import Path


def test_cli_end_to_end(tmp_path, monkeypatch):
    # Create a fake raw article
    art = tmp_path / "raw" / "articles" / "demo"
    art.mkdir(parents=True)
    md = art / "index.md"
    md.write_text("# Demo\n\n![enc](https://example.com/enc.png)\n")

    # Patch httpx.get in a subprocess by using PYTHONPATH + a conftest? Simpler:
    # use a tiny local HTTP server via stdlib
    import http.server, socketserver, threading
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", "4")
            self.end_headers()
            self.wfile.write(b"FAKE")
        def log_message(self, *a, **kw): pass
    srv = socketserver.TCPServer(("127.0.0.1", 0), H)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        md.write_text(f"![enc](http://127.0.0.1:{port}/enc.png)\n")
        r = subprocess.run(
            [sys.executable, "-m", "tools.fetch_images", str(md)],
            capture_output=True, text=True,
        )
        assert r.returncode == 0, f"stderr: {r.stderr}"
        new_text = md.read_text()
        assert "127.0.0.1" not in new_text, f"URL not rewritten: {new_text}"
        assert (art / "img").exists()
        assert any((art / "img").iterdir())
    finally:
        srv.shutdown()


def test_cli_partial_failure_rewrites_successes(tmp_path):
    # One image 404s, the other succeeds. The success must still be downloaded
    # and rewritten; the run reports non-zero but does not crash or discard work.
    import http.server, socketserver, threading
    art = tmp_path / "raw" / "articles" / "demo"
    art.mkdir(parents=True)
    md = art / "index.md"

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.endswith("good.png"):
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", "4")
                self.end_headers()
                self.wfile.write(b"FAKE")
            else:
                self.send_response(404)
                self.end_headers()
        def log_message(self, *a, **kw): pass

    srv = socketserver.TCPServer(("127.0.0.1", 0), H)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        good = f"http://127.0.0.1:{port}/good.png"
        bad = f"http://127.0.0.1:{port}/missing.png"
        md.write_text(f"![g]({good})\n\n![b]({bad})\n")
        r = subprocess.run(
            [sys.executable, "-m", "tools.fetch_images", str(md)],
            capture_output=True, text=True,
        )
        assert r.returncode == 1, r.stdout + r.stderr
        new_text = md.read_text()
        assert good not in new_text                 # success URL rewritten to local path
        assert "img/" in new_text                   # ...with a local replacement
        assert bad in new_text                      # failure left intact
        assert (art / "img").exists() and any((art / "img").iterdir())
    finally:
        srv.shutdown()
