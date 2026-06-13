"""Find remote image URLs in a markdown document."""
from __future__ import annotations
import re

# ![alt](url) — url must start with http(s)://
_MD_IMG = re.compile(r"!\[[^\]]*\]\((https?://[^)]+)\)")
# <img ... src="url" ...>
_HTML_IMG = re.compile(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', re.IGNORECASE)


def extract_remote_image_urls(text: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for m in _MD_IMG.finditer(text):
        url = m.group(1)
        if url not in seen:
            seen.add(url)
            out.append(url)
    for m in _HTML_IMG.finditer(text):
        url = m.group(1)
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out
