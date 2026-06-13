from pathlib import Path
from tools.search.index import build_index
from tools.search.query import query

FIXTURE = Path("tests/fixtures/tiny_base")


def test_query_returns_known_hit():
    idx = build_index(FIXTURE)
    hits = query(idx, "foo")
    assert hits, "expected at least one hit for 'foo'"
    # foo is the title of the source summary at wiki/sources/papers/foo.md
    assert any("foo.md" in h.path for h in hits)


def test_query_is_case_insensitive():
    idx = build_index(FIXTURE)
    assert query(idx, "FOO") == query(idx, "foo")


def test_query_no_results_returns_empty():
    idx = build_index(FIXTURE)
    assert query(idx, "zzzxxxyyy") == []


def test_query_type_filter():
    idx = build_index(FIXTURE)
    hits = query(idx, "bar", type_filter="article")
    assert all(h.type == "article" for h in hits)
