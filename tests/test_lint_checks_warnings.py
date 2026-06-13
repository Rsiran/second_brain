from pathlib import Path
from tools.lint.loader import load_base
from tools.lint.checks import (
    check_orphan_sources,
    check_ungrounded_articles,
    check_dates_sane,
)
from tools.lint.report import Severity

FIXTURE = Path("tests/fixtures/tiny_base")


def test_orphan_sources_passes_on_tiny_base():
    base = load_base(FIXTURE)
    findings = check_orphan_sources(base)
    assert findings == []  # 'foo' is cited by 'bar'


def test_orphan_sources_detects_uncited(tmp_path):
    (tmp_path / "wiki" / "sources" / "papers").mkdir(parents=True)
    (tmp_path / "wiki" / "sources" / "papers" / "lonely.md").write_text(
        "---\ntitle: lonely\ntype: source\nsource_type: paper\n"
        "source_path: raw/papers/lonely.pdf\n"
        "ingested: 2026-01-01\ntags: []\n---\n"
    )
    base = load_base(tmp_path)
    findings = check_orphan_sources(base)
    assert any("lonely" in f.message for f in findings)
    assert all(f.severity == Severity.WARNING for f in findings)


def test_ungrounded_articles_passes_on_tiny_base():
    base = load_base(FIXTURE)
    findings = check_ungrounded_articles(base)
    assert findings == []


def test_ungrounded_articles_detects_missing_sources(tmp_path):
    (tmp_path / "wiki" / "articles").mkdir(parents=True)
    (tmp_path / "wiki" / "articles" / "floating.md").write_text(
        "---\ntitle: floating\ntype: article\ncreated: 2026-01-01\n"
        "updated: 2026-01-01\ntags: []\n---\nno sources cited\n"
    )
    base = load_base(tmp_path)
    findings = check_ungrounded_articles(base)
    assert any("floating" in f.file for f in findings)
    assert all(f.severity == Severity.WARNING for f in findings)


def test_dates_sane_passes_on_tiny_base():
    base = load_base(FIXTURE)
    findings = check_dates_sane(base, today="2026-04-09")
    assert findings == []


def test_dates_sane_detects_future(tmp_path):
    (tmp_path / "wiki" / "articles").mkdir(parents=True)
    (tmp_path / "wiki" / "articles" / "x.md").write_text(
        "---\ntitle: x\ntype: article\ncreated: 2099-01-01\n"
        "updated: 2099-01-02\ntags: []\n---\n"
    )
    base = load_base(tmp_path)
    findings = check_dates_sane(base, today="2026-04-09")
    assert len(findings) >= 1
    assert all(f.severity == Severity.WARNING for f in findings)
