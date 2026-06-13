"""Output frontmatter schema definition and validation."""
from __future__ import annotations
from datetime import date

VALID_FORMATS = {"report", "slides", "chart", "mixed"}

SCHEMA = {
    "required": {"title", "type", "query", "created", "format", "tags"},
    "optional": {"sources_consulted", "filed_back", "filed_back_as"},
}


def _is_iso_date(value) -> bool:
    if isinstance(value, date):
        return True
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def validate_output_frontmatter(meta: dict) -> list[str]:
    """Return a list of human-readable error strings. Empty list = valid."""
    errors: list[str] = []

    t = meta.get("type")
    if t != "output":
        errors.append(f"type: must be 'output', got {t!r}")
        return errors

    for field in SCHEMA["required"]:
        if field not in meta:
            errors.append(f"{field}: required field missing")

    fmt = meta.get("format")
    if fmt is not None and fmt not in VALID_FORMATS:
        errors.append(f"format: must be one of {sorted(VALID_FORMATS)}, got {fmt!r}")

    if "created" in meta and not _is_iso_date(meta["created"]):
        errors.append(f"created: must be an ISO date (YYYY-MM-DD), got {meta['created']!r}")

    if "tags" in meta and not isinstance(meta["tags"], list):
        errors.append("tags: must be a list")

    if "sources_consulted" in meta and not isinstance(meta["sources_consulted"], list):
        errors.append("sources_consulted: must be a list")

    if "filed_back" in meta and not isinstance(meta["filed_back"], bool):
        errors.append(f"filed_back: must be a boolean, got {meta['filed_back']!r}")

    return errors
