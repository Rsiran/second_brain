from pathlib import Path
from unittest.mock import patch

from tools.render.marp import render_marp, find_marp


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_missing_slides(tmp_path):
    bundle = tmp_path / "2026-04-01-test"
    bundle.mkdir()
    success, msg = render_marp(bundle)
    assert not success
    assert "slides.md not found" in msg


def test_marp_not_on_path(tmp_path):
    bundle = tmp_path / "2026-04-01-test"
    _write(bundle / "slides.md", "---\nmarp: true\n---\nSlide\n")
    with patch("tools.render.marp.find_marp", return_value=None):
        success, msg = render_marp(bundle)
    assert not success
    assert "not found on PATH" in msg
    assert "npm install" in msg


def test_find_marp_returns_something_or_none():
    # Just ensure it doesn't crash
    result = find_marp()
    assert result is None or isinstance(result, str)
