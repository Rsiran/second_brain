from tools.render.schema import validate_output_frontmatter


def _valid_meta():
    return {
        "title": "Test",
        "type": "output",
        "query": "What is attention?",
        "created": "2026-04-01",
        "format": "report",
        "tags": ["test"],
    }


def test_valid():
    assert validate_output_frontmatter(_valid_meta()) == []


def test_wrong_type():
    meta = _valid_meta()
    meta["type"] = "article"
    errors = validate_output_frontmatter(meta)
    assert any("type" in e for e in errors)


def test_missing_required():
    meta = {"type": "output", "title": "X"}
    errors = validate_output_frontmatter(meta)
    assert len(errors) >= 3  # missing query, created, format, tags


def test_invalid_format():
    meta = _valid_meta()
    meta["format"] = "pdf"
    errors = validate_output_frontmatter(meta)
    assert any("format" in e for e in errors)


def test_invalid_date():
    meta = _valid_meta()
    meta["created"] = "not-a-date"
    errors = validate_output_frontmatter(meta)
    assert any("created" in e for e in errors)


def test_tags_not_list():
    meta = _valid_meta()
    meta["tags"] = "single"
    errors = validate_output_frontmatter(meta)
    assert any("tags" in e for e in errors)


def test_filed_back_not_bool():
    meta = _valid_meta()
    meta["filed_back"] = "yes"
    errors = validate_output_frontmatter(meta)
    assert any("filed_back" in e for e in errors)


def test_filed_back_bool_ok():
    meta = _valid_meta()
    meta["filed_back"] = True
    assert validate_output_frontmatter(meta) == []


def test_sources_consulted_not_list():
    meta = _valid_meta()
    meta["sources_consulted"] = "single"
    errors = validate_output_frontmatter(meta)
    assert any("sources_consulted" in e for e in errors)


def test_all_formats_valid():
    for fmt in ("report", "slides", "chart", "mixed"):
        meta = _valid_meta()
        meta["format"] = fmt
        assert validate_output_frontmatter(meta) == []
