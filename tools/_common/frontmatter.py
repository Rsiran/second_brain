"""Minimal YAML-frontmatter parser. Splits a markdown document into (metadata, body)."""
from __future__ import annotations
import yaml

_BOM = "\ufeff"


class FrontmatterError(ValueError):
    """Raised when a file's YAML frontmatter is missing or malformed."""


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse a markdown string with YAML frontmatter.

    Returns (metadata_dict, body_string). Raises FrontmatterError if the
    document does not start with `---` or the frontmatter is unclosed.
    """
    if text[:1] == _BOM:
        text = text[1:]  # tolerate a leading UTF-8 BOM
    if not text.startswith("---"):
        raise FrontmatterError("file does not start with '---'")
    lines = text.splitlines(keepends=True)
    # Find the closing '---' line (after the opening)
    closing = None
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            closing = i
            break
    if closing is None:
        raise FrontmatterError("frontmatter has no closing '---'")
    yaml_text = "".join(lines[1:closing])
    try:
        meta = yaml.safe_load(yaml_text) or {}
    except yaml.YAMLError as e:
        raise FrontmatterError(f"invalid YAML: {e}") from e
    if not isinstance(meta, dict):
        raise FrontmatterError("frontmatter YAML must be a mapping")
    body = "".join(lines[closing + 1 :]).lstrip("\n")
    return meta, body
