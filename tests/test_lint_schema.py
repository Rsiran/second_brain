from tools.lint.schema import validate_frontmatter, SCHEMAS


def test_valid_source_passes():
    meta = {
        "title": "Paper",
        "type": "source",
        "source_type": "paper",
        "source_path": "raw/papers/x.pdf",
        "ingested": "2026-03-10",
        "tags": ["ml"],
    }
    errors = validate_frontmatter(meta)
    assert errors == []


def test_source_missing_required_field():
    meta = {"title": "x", "type": "source"}  # missing source_type, source_path, ingested
    errors = validate_frontmatter(meta)
    assert any("source_type" in e for e in errors)
    assert any("source_path" in e for e in errors)
    assert any("ingested" in e for e in errors)


def test_valid_article_passes():
    meta = {
        "title": "Transformers",
        "type": "article",
        "created": "2026-03-10",
        "updated": "2026-03-10",
        "tags": ["ml"],
        "sources": ["[[x]]"],
        "related": ["[[y]]"],
    }
    assert validate_frontmatter(meta) == []


def test_article_missing_sources_is_allowed_at_schema_level():
    # Schema allows missing 'sources'; the lint 'ungrounded article' check is separate
    meta = {
        "title": "x",
        "type": "article",
        "created": "2026-03-10",
        "updated": "2026-03-10",
        "tags": [],
    }
    assert validate_frontmatter(meta) == []


def test_valid_index_passes():
    meta = {"title": "By topic", "type": "index", "generated": "2026-03-15"}
    assert validate_frontmatter(meta) == []


def test_unknown_type_rejected():
    errors = validate_frontmatter({"title": "x", "type": "other"})
    assert any("type" in e for e in errors)


def test_bad_date_format_rejected():
    meta = {
        "title": "x",
        "type": "source",
        "source_type": "paper",
        "source_path": "raw/papers/x.pdf",
        "ingested": "March 10 2026",
        "tags": [],
    }
    errors = validate_frontmatter(meta)
    assert any("ingested" in e for e in errors)


def _source(**extra):
    meta = {
        "title": "Paper",
        "type": "source",
        "source_type": "paper",
        "source_path": "raw/papers/x.pdf",
        "ingested": "2026-03-10",
        "tags": ["ml"],
    }
    meta.update(extra)
    return meta


def test_valid_extraction_values_pass():
    for ex in ("full-text", "abstract-only", "reference-only", "snapshot-2026-05-06"):
        assert validate_frontmatter(_source(extraction=ex)) == [], ex


def test_bad_extraction_value_rejected():
    errors = validate_frontmatter(_source(extraction="partial"))
    assert any("extraction" in e for e in errors)


def test_bad_snapshot_date_rejected():
    errors = validate_frontmatter(_source(extraction="snapshot-not-a-date"))
    assert any("extraction" in e for e in errors)


def test_missing_extraction_is_allowed():
    # extraction is optional at schema level (mini-base sources omit it).
    assert validate_frontmatter(_source()) == []


def _art(**extra):
    meta = {
        "title": "A",
        "type": "article",
        "created": "2026-03-10",
        "updated": "2026-03-10",
        "tags": [],
    }
    meta.update(extra)
    return meta


def test_valid_zone_values_pass():
    for z in ("domain", "product", "market"):
        assert validate_frontmatter(_art(zone=z)) == [], z


def test_bad_zone_rejected():
    errors = validate_frontmatter(_art(zone="internal"))
    assert any("zone" in e for e in errors)


def test_missing_zone_is_allowed():
    assert validate_frontmatter(_art()) == []
