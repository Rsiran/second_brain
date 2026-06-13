"""Slug derivation from raw file paths."""
from __future__ import annotations
from pathlib import Path


def raw_path_to_source_slug(rel: str) -> tuple[str, str] | None:
    """Derive (source_type, slug) from a raw-relative path.

    Examples:
        raw/papers/foo.pdf.placeholder     -> ("papers", "foo")
        raw/articles/the-x/index.md        -> ("articles", "the-x")
        raw/articles/the-x/img/encoder.png -> None  (subordinate file)
        raw/notes/2026-03-15.md            -> ("notes", "2026-03-15")
        raw/datasets/glue/README.md        -> ("datasets", "glue")
    """
    parts = Path(rel).parts
    if len(parts) < 3 or parts[0] != "raw":
        return None
    type_ = parts[1]
    if len(parts) == 3:
        name = parts[2]
        if name.startswith("."):
            return None  # dotfile (.DS_Store, .gitkeep, …), not a source doc
        # Drop a trailing '.placeholder', then a single real extension.
        # (split-at-first-dot would truncate 'yolo-v2.5-survey.pdf' to 'yolo-v2'.)
        if name.endswith(".placeholder"):
            name = name[: -len(".placeholder")]
        slug = Path(name).stem
        if not slug:
            return None
        return (type_, slug)
    if len(parts) == 4 and parts[3] in ("index.md", "index.html", "README.md"):
        return (type_, parts[2])
    if len(parts) >= 4 and parts[3] == "img":
        return None  # image inside an article folder, not a standalone raw doc
    # deeper raw asset that is not the canonical index: ignore
    return None
