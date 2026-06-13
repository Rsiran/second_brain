import os
import time
from pathlib import Path

from tools.ingest.diff import compute_ingest_diff


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _source_fm(title: str, source_type: str, source_path: str, ingested: str = "2026-01-01"):
    return (
        f"---\ntitle: {title}\ntype: source\nsource_type: {source_type}\n"
        f"source_path: {source_path}\ningested: {ingested}\ntags: []\n---\n"
    )


def test_empty_base(tmp_path):
    (tmp_path / "raw").mkdir()
    (tmp_path / "wiki").mkdir()
    diff = compute_ingest_diff(tmp_path)
    assert diff.total == 0
    assert diff.summary == "0 new, 0 modified, 0 orphaned"


def test_new_items_detected(tmp_path):
    _write(tmp_path / "raw" / "papers" / "foo.pdf.placeholder", "")
    _write(tmp_path / "raw" / "notes" / "bar.md", "---\ntitle: bar\n---\nsome note\n")
    (tmp_path / "wiki" / "sources").mkdir(parents=True)
    diff = compute_ingest_diff(tmp_path)
    assert len(diff.new) == 2
    slugs = {i.slug for i in diff.new}
    assert slugs == {"foo", "bar"}


def test_synced_base_has_no_diff(tmp_path):
    _write(tmp_path / "raw" / "papers" / "foo.pdf.placeholder", "")
    _write(
        tmp_path / "wiki" / "sources" / "papers" / "foo.md",
        _source_fm("Foo", "paper", "raw/papers/foo.pdf.placeholder", "2099-12-31"),
    )
    diff = compute_ingest_diff(tmp_path)
    assert len(diff.new) == 0
    assert len(diff.orphaned) == 0


def test_orphaned_source_detected(tmp_path):
    # Source exists in wiki but raw file was deleted
    (tmp_path / "raw").mkdir()
    _write(
        tmp_path / "wiki" / "sources" / "papers" / "ghost.md",
        _source_fm("Ghost", "paper", "raw/papers/ghost.pdf.placeholder"),
    )
    diff = compute_ingest_diff(tmp_path)
    assert len(diff.orphaned) == 1
    assert diff.orphaned[0].source_path == "wiki/sources/papers/ghost.md"


def test_modified_detected_when_raw_newer(tmp_path):
    # Create the source summary with an old ingested date
    _write(
        tmp_path / "wiki" / "sources" / "notes" / "meeting.md",
        _source_fm("Meeting", "note", "raw/notes/meeting.md", "2020-01-01"),
    )
    # Create the raw file (its mtime will be "now", well after 2020-01-01)
    _write(tmp_path / "raw" / "notes" / "meeting.md", "some content\n")
    diff = compute_ingest_diff(tmp_path)
    assert len(diff.modified) == 1
    assert diff.modified[0].slug == "meeting"
    assert diff.modified[0].ingested == "2020-01-01"


def test_not_modified_when_raw_older(tmp_path):
    # Create raw file
    raw_path = tmp_path / "raw" / "notes" / "old.md"
    _write(raw_path, "content\n")
    # Set its mtime to the past
    old_ts = time.mktime(time.strptime("2019-01-01", "%Y-%m-%d"))
    os.utime(raw_path, (old_ts, old_ts))
    # Source with a later ingested date
    _write(
        tmp_path / "wiki" / "sources" / "notes" / "old.md",
        _source_fm("Old", "note", "raw/notes/old.md", "2020-06-01"),
    )
    diff = compute_ingest_diff(tmp_path)
    assert len(diff.modified) == 0


def test_source_from_shared_note_is_not_orphaned(tmp_path):
    # A source distilled from a shared note points at that note via source_path;
    # it has no raw/<type>/<slug> file but is NOT orphaned because the note exists.
    _write(tmp_path / "raw" / "notes" / "reading-list.md", "- some paper\n")
    _write(
        tmp_path / "wiki" / "sources" / "papers" / "some-paper.md",
        _source_fm("Some Paper", "paper", "raw/notes/reading-list.md"),
    )
    diff = compute_ingest_diff(tmp_path)
    assert diff.orphaned == []


def test_source_with_missing_source_path_is_orphaned(tmp_path):
    (tmp_path / "raw").mkdir()
    _write(
        tmp_path / "wiki" / "sources" / "papers" / "ghost.md",
        _source_fm("Ghost", "paper", "raw/notes/does-not-exist.md"),
    )
    diff = compute_ingest_diff(tmp_path)
    assert len(diff.orphaned) == 1
    assert diff.orphaned[0].source_path == "wiki/sources/papers/ghost.md"


def test_modified_failsafe_on_unparseable_ingested_date(tmp_path):
    # A source whose ingested date can't be parsed must not silently vanish:
    # the raw file is reported as modified so the drift surfaces.
    _write(tmp_path / "raw" / "notes" / "n.md", "content\n")
    _write(
        tmp_path / "wiki" / "sources" / "notes" / "n.md",
        _source_fm("N", "note", "raw/notes/n.md", ingested="not-a-date"),
    )
    diff = compute_ingest_diff(tmp_path)
    assert [m.slug for m in diff.modified] == ["n"]


def test_mini_base_fixture():
    """The mini-base should report zero new and zero orphaned."""
    diff = compute_ingest_diff(Path("examples/mini-base"))
    assert len(diff.new) == 0
    assert len(diff.orphaned) == 0


def test_to_dict_structure(tmp_path):
    _write(tmp_path / "raw" / "papers" / "a.pdf.placeholder", "")
    (tmp_path / "wiki" / "sources").mkdir(parents=True)
    diff = compute_ingest_diff(tmp_path)
    d = diff.to_dict()
    assert "new" in d
    assert "modified" in d
    assert "orphaned" in d
    assert "summary" in d
    assert len(d["new"]) == 1
    assert d["new"][0]["slug"] == "a"
