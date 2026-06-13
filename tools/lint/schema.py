"""Frontmatter schema definitions and validation for wiki files."""
from __future__ import annotations
from datetime import date

VALID_TYPES = {"source", "article", "index"}
VALID_ZONES = {"domain", "product", "market"}
# extraction values per CLAUDE.md §3; snapshot carries a trailing ISO date.
VALID_EXTRACTIONS = {"full-text", "abstract-only", "reference-only"}
# Source kinds the KB recognizes. See CLAUDE.md §2 for what each one is for.
# Extend this set if your domain needs additional source types.
VALID_SOURCE_TYPES = {
    # Generic media types
    "article", "paper", "repo", "dataset", "image", "note",
    # Organizational / subject types
    "spec", "meeting", "competitor", "regulation", "standard",
    "datasheet", "incident", "book",
}

# Required fields per type. 'title' and 'type' are always required.
SCHEMAS: dict[str, dict[str, set[str]]] = {
    "source": {
        "required": {"title", "type", "source_type", "source_path", "ingested", "tags"},
        "optional": {"source_url", "authors"},
    },
    "article": {
        "required": {"title", "type", "created", "updated", "tags"},
        "optional": {"sources", "related"},
    },
    "index": {
        "required": {"title", "type", "generated"},
        "optional": set(),
    },
}

_DATE_FIELDS = {"ingested", "created", "updated", "generated"}


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


def _is_valid_extraction(value) -> bool:
    if value in VALID_EXTRACTIONS:
        return True
    if isinstance(value, str) and value.startswith("snapshot-"):
        return _is_iso_date(value[len("snapshot-"):])
    return False


def validate_frontmatter(meta: dict) -> list[str]:
    """Return a list of human-readable error strings. Empty list = valid."""
    errors: list[str] = []
    t = meta.get("type")
    if t not in VALID_TYPES:
        errors.append(f"type: must be one of {sorted(VALID_TYPES)}, got {t!r}")
        return errors  # further checks need a valid type

    schema = SCHEMAS[t]
    for field in schema["required"]:
        if field not in meta:
            errors.append(f"{field}: required field missing")

    if t == "source":
        st = meta.get("source_type")
        if st is not None and st not in VALID_SOURCE_TYPES:
            errors.append(
                f"source_type: must be one of {sorted(VALID_SOURCE_TYPES)}, got {st!r}"
            )
        ex = meta.get("extraction")
        if ex is not None and not _is_valid_extraction(ex):
            errors.append(
                "extraction: must be one of "
                f"{sorted(VALID_EXTRACTIONS)} or 'snapshot-YYYY-MM-DD', got {ex!r}"
            )

    if t == "article":
        zone = meta.get("zone")
        if zone is not None and zone not in VALID_ZONES:
            errors.append(f"zone: must be one of {sorted(VALID_ZONES)}, got {zone!r}")

    for field in _DATE_FIELDS & meta.keys():
        if not _is_iso_date(meta[field]):
            errors.append(f"{field}: must be an ISO date (YYYY-MM-DD), got {meta[field]!r}")

    # tags must be a list if present
    if "tags" in meta and not isinstance(meta["tags"], list):
        errors.append("tags: must be a list")

    return errors
