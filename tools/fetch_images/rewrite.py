"""Rewrite remote image URLs in markdown to local paths."""
from __future__ import annotations


def rewrite_urls(text: str, mapping: dict[str, str]) -> str:
    """Replace every occurrence of each remote URL with its local replacement.

    Simple string-replace. Order keys from longest to shortest so a URL that is
    a prefix of another doesn't cause partial replacements.
    """
    for url in sorted(mapping, key=len, reverse=True):
        text = text.replace(url, mapping[url])
    return text
