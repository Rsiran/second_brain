"""Download a remote image to a local folder. Idempotent: existing files skipped."""
from __future__ import annotations
import glob
import hashlib
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import httpx

_CONTENT_TYPE_EXT = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/svg+xml": "svg",
    "image/bmp": "bmp",
    "image/avif": "avif",
}


def _stem_for_url(url: str) -> str:
    parsed = urlparse(url)
    path_name = Path(parsed.path).name
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
    if "." in path_name:
        return f"{h}-{path_name.rsplit('.', 1)[0]}"
    if path_name:
        return f"{h}-{path_name}"
    return h


def _ext_from_url(url: str) -> str | None:
    """Extension from URL path, or from a ``?format=`` query parameter."""
    parsed = urlparse(url)
    path_name = Path(parsed.path).name
    if "." in path_name:
        return path_name.rsplit(".", 1)[1].lower()
    fmt = parse_qs(parsed.query).get("format", [None])[0]
    return fmt.lower() if fmt else None


def _ext_from_content_type(content_type: str | None) -> str | None:
    if not content_type:
        return None
    return _CONTENT_TYPE_EXT.get(content_type.split(";")[0].strip().lower())


def _filename_for_url(url: str) -> str:
    """Deterministic URL-only filename guess. Falls through to ``.bin`` when the URL carries no format hint."""
    return f"{_stem_for_url(url)}.{_ext_from_url(url) or 'bin'}"


def download_image(url: str, dest_dir: Path, *, timeout: int = 30) -> Path:
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    stem = _stem_for_url(url)
    # escape glob metacharacters that can appear in URL-derived stems, else the
    # idempotency check silently misses or mismatches existing downloads.
    existing = sorted(dest_dir.glob(f"{glob.escape(stem)}.*"))
    if existing:
        return existing[0]
    resp = httpx.get(url, timeout=timeout, follow_redirects=True)
    resp.raise_for_status()
    ext = (
        _ext_from_url(url)
        or _ext_from_content_type(getattr(resp, "headers", {}).get("content-type"))
        or "bin"
    )
    dest = dest_dir / f"{stem}.{ext}"
    # Write atomically so an interrupted download never leaves a half-written
    # file that the idempotency glob would then return forever.
    tmp = dest.with_name(dest.name + ".part")
    tmp.write_bytes(resp.content)
    os.replace(tmp, dest)
    return dest
