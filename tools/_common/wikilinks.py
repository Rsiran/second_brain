"""Extract Obsidian-style wikilinks from markdown text."""
from __future__ import annotations
import re
from pathlib import Path

# Matches [[target]] or [[target|display]] or ![[target]]
WIKILINK_RE = re.compile(r"!?\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")


def extract_wikilinks(text: str) -> list[str]:
    """Return the list of wikilink targets in order of appearance.

    Targets are returned verbatim (fragments and extensions intact). Use
    ``link_target_slug`` to normalize a target to the slug it resolves to.
    """
    return [m.group(1).strip() for m in WIKILINK_RE.finditer(text)]


def link_target_slug(target: str) -> str | None:
    """Normalize a wikilink target to the wiki slug it should resolve to.

    Strips Obsidian heading/block fragments (``note#section``, ``note#^block``)
    and any path prefix. Returns None for asset embeds (``diagram.png``), which
    point at files outside the wiki/*.md slug space and so are not note links,
    and for pure in-page fragments (``#heading``).
    """
    target = target.split("#", 1)[0].strip()
    if not target:
        return None
    name = Path(target).name
    suffix = Path(name).suffix.lower()
    if suffix and suffix != ".md":
        return None  # asset embed, not a note link
    return Path(name).stem if suffix == ".md" else name
