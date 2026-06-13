"""Helpers to derive the zone label and slug from a wiki/-relative path.

The MCP server uses these to enrich search results with `zone` and `slug`
fields the agent can reason about. Pure path manipulation, no I/O.
"""
from __future__ import annotations
from pathlib import Path


def zone_for_path(path: Path) -> str | None:
    """Return the zone label for a path inside `wiki/`.

    The zone is the first path component after `wiki/`. Returns the bare
    string `"wiki"` for top-level files like `wiki/README.md`, and `None`
    for paths outside the `wiki/` tree.
    """
    parts = path.parts
    if "wiki" not in parts:
        return None
    i = parts.index("wiki")
    after = parts[i + 1 :]
    if not after:
        return None
    if len(after) == 1:
        # Top-level file in wiki/, e.g. wiki/README.md
        return "wiki"
    return after[0]


def slug_for_path(path: Path) -> str:
    """Return the slug (filename without extension) for any markdown path."""
    return path.stem
