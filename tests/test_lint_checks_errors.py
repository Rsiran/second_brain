from pathlib import Path
from tools.lint.loader import load_base
from tools.lint.checks import (
    check_sources_mirror_raw,
    check_source_paths_exist,
    check_frontmatter_schemas,
    check_wikilinks_resolve,
    check_duplicate_slugs,
)
from tools.lint.report import Severity

FIXTURE = Path("tests/fixtures/tiny_base")


def _article(tmp_path, slug: str, body: str = "") -> None:
    d = tmp_path / "wiki" / "articles"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{slug}.md").write_text(
        "---\ntitle: t\ntype: article\ncreated: 2026-01-01\n"
        f"updated: 2026-01-01\ntags: []\n---\n\n{body}\n"
    )


def test_sources_mirror_raw_passes_on_tiny_base():
    base = load_base(FIXTURE)
    findings = check_sources_mirror_raw(base)
    assert findings == []


def test_sources_mirror_raw_detects_missing_summary(tmp_path):
    # Build a base with a raw file but no matching source summary
    (tmp_path / "raw" / "papers").mkdir(parents=True)
    (tmp_path / "raw" / "papers" / "orphan.pdf.placeholder").touch()
    (tmp_path / "wiki").mkdir()
    base = load_base(tmp_path)
    findings = check_sources_mirror_raw(base)
    assert any("orphan" in f.message for f in findings)
    assert all(f.severity == Severity.ERROR for f in findings)


def test_source_paths_exist_passes_on_tiny_base():
    base = load_base(FIXTURE)
    findings = check_source_paths_exist(base)
    assert findings == []


def test_source_paths_exist_detects_dangling(tmp_path):
    (tmp_path / "wiki" / "sources" / "papers").mkdir(parents=True)
    (tmp_path / "wiki" / "sources" / "papers" / "ghost.md").write_text(
        "---\ntitle: g\ntype: source\nsource_type: paper\n"
        "source_path: raw/papers/does-not-exist.pdf\n"
        "ingested: 2026-01-01\ntags: []\n---\n"
    )
    base = load_base(tmp_path)
    findings = check_source_paths_exist(base)
    assert any("does-not-exist" in f.message for f in findings)


def test_frontmatter_schemas_passes_on_tiny_base():
    base = load_base(FIXTURE)
    findings = check_frontmatter_schemas(base)
    assert findings == []


def test_frontmatter_schemas_detects_bad_file(tmp_path):
    (tmp_path / "wiki" / "articles").mkdir(parents=True)
    (tmp_path / "wiki" / "articles" / "x.md").write_text(
        "---\ntitle: x\ntype: article\n---\n"  # missing created/updated/tags
    )
    base = load_base(tmp_path)
    findings = check_frontmatter_schemas(base)
    assert len(findings) >= 1
    assert all(f.severity == Severity.ERROR for f in findings)


def test_wikilinks_resolve_passes_on_tiny_base():
    base = load_base(FIXTURE)
    findings = check_wikilinks_resolve(base)
    assert findings == []


def test_wikilinks_resolve_detects_broken(tmp_path):
    (tmp_path / "wiki" / "articles").mkdir(parents=True)
    (tmp_path / "wiki" / "articles" / "x.md").write_text(
        "---\ntitle: x\ntype: article\ncreated: 2026-01-01\n"
        "updated: 2026-01-01\ntags: []\n---\n\nSee [[ghost]].\n"
    )
    base = load_base(tmp_path)
    findings = check_wikilinks_resolve(base)
    assert any("ghost" in f.message for f in findings)


def test_wikilinks_resolve_ignores_heading_anchor(tmp_path):
    # [[target#section]] resolves to 'target', not the literal 'target#section'.
    _article(tmp_path, "target")
    _article(tmp_path, "x", body="See [[target#some-heading]] and [[target#^block-id]].")
    base = load_base(tmp_path)
    assert check_wikilinks_resolve(base) == []


def test_wikilinks_resolve_skips_asset_embeds(tmp_path):
    # ![[diagram.png]] points at an asset, not a wiki note — never a broken link.
    _article(tmp_path, "x", body="Figure: ![[diagram.png]] and ![[chart.svg]]")
    base = load_base(tmp_path)
    assert check_wikilinks_resolve(base) == []


def test_duplicate_slugs_passes_on_tiny_base():
    base = load_base(FIXTURE)
    assert check_duplicate_slugs(base) == []


def test_duplicate_slugs_detects_collision(tmp_path):
    (tmp_path / "wiki" / "domain" / "articles").mkdir(parents=True)
    (tmp_path / "wiki" / "market" / "articles").mkdir(parents=True)
    for zone in ("domain", "market"):
        (tmp_path / "wiki" / zone / "articles" / "transformer.md").write_text(
            "---\ntitle: s\ntype: article\ncreated: 2026-01-01\n"
            "updated: 2026-01-01\ntags: []\n---\n"
        )
    base = load_base(tmp_path)
    findings = check_duplicate_slugs(base)
    assert findings, "collision on 'transformer' should be reported"
    assert all(f.severity == Severity.ERROR for f in findings)
    assert all("transformer" in f.message for f in findings)


def test_duplicate_slugs_allows_repeated_readme(tmp_path):
    (tmp_path / "wiki" / "domain").mkdir(parents=True)
    (tmp_path / "wiki" / "market").mkdir(parents=True)
    for zone in ("domain", "market"):
        (tmp_path / "wiki" / zone / "README.md").write_text(
            "---\ntitle: idx\ntype: index\ngenerated: 2026-01-01\n---\n"
        )
    base = load_base(tmp_path)
    assert check_duplicate_slugs(base) == []
