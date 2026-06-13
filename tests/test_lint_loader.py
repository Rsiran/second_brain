from pathlib import Path
from tools.lint.loader import load_base, LoadedFile

FIXTURE = Path("tests/fixtures/tiny_base")


def test_load_base_finds_all_wiki_files():
    base = load_base(FIXTURE)
    paths = sorted(f.relative_path for f in base.wiki_files)
    assert "wiki/README.md" in paths
    assert "wiki/sources/papers/foo.md" in paths
    assert "wiki/articles/bar.md" in paths
    assert "wiki/indexes/by-topic.md" in paths


def test_load_base_finds_raw_files():
    base = load_base(FIXTURE)
    raw_paths = sorted(base.raw_files)
    assert "raw/papers/foo.pdf.placeholder" in raw_paths


def test_loaded_file_has_parsed_frontmatter():
    base = load_base(FIXTURE)
    by_path = {f.relative_path: f for f in base.wiki_files}
    foo = by_path["wiki/sources/papers/foo.md"]
    assert foo.meta["title"] == "Foo"
    assert foo.meta["type"] == "source"
    assert foo.wikilinks == []  # body has none


def test_loaded_file_extracts_body_wikilinks():
    base = load_base(FIXTURE)
    by_path = {f.relative_path: f for f in base.wiki_files}
    bar = by_path["wiki/articles/bar.md"]
    assert bar.wikilinks == ["foo"]
