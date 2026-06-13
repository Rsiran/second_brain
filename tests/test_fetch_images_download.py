from pathlib import Path
from tools.fetch_images.download import download_image, _filename_for_url


def test_filename_for_url_is_stable_and_keeps_extension():
    n1 = _filename_for_url("https://example.com/images/foo.png")
    n2 = _filename_for_url("https://example.com/images/foo.png")
    assert n1 == n2
    assert n1.endswith(".png")


def test_filename_for_url_handles_no_extension():
    n = _filename_for_url("https://example.com/noext")
    assert "." not in n or n.endswith(".bin")


def test_filename_for_url_uses_format_query_param():
    n = _filename_for_url("https://pbs.twimg.com/media/HE7cYBCaIAALxvf?format=jpg&name=large")
    assert n.endswith(".jpg")


def test_download_uses_content_type_when_url_lacks_extension(tmp_path, monkeypatch):
    class FakeResp:
        status_code = 200
        content = b"\x89PNG\r\n\x1a\nFAKE"
        headers = {"content-type": "image/png; charset=binary"}
        def raise_for_status(self): pass
    def fake_get(url, timeout=30, follow_redirects=True):
        return FakeResp()
    import tools.fetch_images.download as mod
    monkeypatch.setattr(mod.httpx, "get", fake_get)

    dest = tmp_path / "img"
    path = download_image("https://example.com/opaque-id", dest)
    assert path.suffix == ".png"


def test_download_writes_file(tmp_path, monkeypatch):
    class FakeResp:
        status_code = 200
        content = b"\x89PNG\r\n\x1a\nFAKE"
        def raise_for_status(self): pass
    def fake_get(url, timeout=30, follow_redirects=True):
        return FakeResp()
    import tools.fetch_images.download as mod
    monkeypatch.setattr(mod.httpx, "get", fake_get)

    dest_dir = tmp_path / "img"
    path = download_image("https://example.com/a.png", dest_dir)
    assert path.exists()
    assert path.read_bytes() == b"\x89PNG\r\n\x1a\nFAKE"


def test_download_is_idempotent(tmp_path, monkeypatch):
    calls = {"n": 0}
    class FakeResp:
        status_code = 200
        content = b"DATA"
        def raise_for_status(self): pass
    def fake_get(url, timeout=30, follow_redirects=True):
        calls["n"] += 1
        return FakeResp()
    import tools.fetch_images.download as mod
    monkeypatch.setattr(mod.httpx, "get", fake_get)

    dest = tmp_path / "img"
    p1 = download_image("https://example.com/a.png", dest)
    p2 = download_image("https://example.com/a.png", dest)
    assert p1 == p2
    assert calls["n"] == 1  # second call short-circuited
