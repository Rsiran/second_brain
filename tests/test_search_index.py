import os
import time
from pathlib import Path
from tools.search.index import build_index, save_index, index_is_stale

FIXTURE = Path("tests/fixtures/tiny_base")


def test_build_index_from_fixture():
    idx = build_index(FIXTURE)
    # 'foo' appears in a source summary title and body
    assert "foo" in idx.postings
    # 'bar' appears in the article title
    assert "bar" in idx.postings
    # Each posting is a list of (doc_id, count) tuples
    assert all(isinstance(p, list) for p in idx.postings.values())


def test_index_doc_ids_are_wiki_paths():
    idx = build_index(FIXTURE)
    assert any("wiki/articles/bar.md" in doc for doc in idx.documents)


def test_build_index_tolerates_non_utf8_file(tmp_path):
    # One undecodable file must not abort the whole index build.
    wiki = tmp_path / "wiki" / "articles"
    wiki.mkdir(parents=True)
    (wiki / "ok.md").write_text(
        "---\ntitle: Ok\ntype: article\ncreated: 2026-01-01\n"
        "updated: 2026-01-01\ntags: []\n---\n\nclean body\n",
        encoding="utf-8",
    )
    (wiki / "broken.md").write_bytes(b"---\ntitle: B\n---\n\n\xff\xfe not utf-8\n")
    idx = build_index(tmp_path)
    assert any("ok.md" in d for d in idx.documents)
    assert any("broken.md" in d for d in idx.documents)
    assert "clean" in idx.postings


def test_index_is_stale_detects_newer_wiki_file(tmp_path):
    wiki = tmp_path / "wiki" / "articles"
    wiki.mkdir(parents=True)
    art = wiki / "a.md"
    art.write_text(
        "---\ntitle: A\ntype: article\ncreated: 2026-01-01\n"
        "updated: 2026-01-01\ntags: []\n---\n\nbody\n"
    )
    index_path = tmp_path / "index.json"
    save_index(build_index(tmp_path), index_path)
    assert index_is_stale(index_path, tmp_path) is False

    # Touch a wiki file to a time after the index was written.
    future = time.time() + 10
    os.utime(art, (future, future))
    assert index_is_stale(index_path, tmp_path) is True


def test_index_is_stale_false_when_index_missing(tmp_path):
    # Missing index is a distinct condition handled separately by callers.
    assert index_is_stale(tmp_path / "nope.json", tmp_path) is False
