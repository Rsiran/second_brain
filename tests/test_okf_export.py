"""Tests for the OKF export bridge (tools.okf.export)."""
from __future__ import annotations
import hashlib
from pathlib import Path

import pytest

from tools._common.frontmatter import parse_frontmatter
from tools.okf.export import (
    OKF_VERSION,
    build_concept_index,
    export_okf,
    references_section,
    rewrite_body_links,
    rewrite_frontmatter_refs,
)

REPO = Path(__file__).resolve().parents[1]
MINI_WIKI = REPO / "examples" / "mini-base" / "wiki"


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def make_wiki(root: Path) -> Path:
    """A tiny three-file wiki with cross-references for unit tests."""
    wiki = root / "wiki"
    _write(wiki / "domain" / "articles" / "self-attention.md",
        "---\ntitle: Self-Attention\ntype: article\ncreated: 2026-01-01\n"
        "updated: 2026-01-01\ntags: []\n"
        'sources:\n  - "[[attention-paper]]"\n'
        'related:\n  - "[[positional-encoding]]"\n---\n\n'
        "Builds on [[positional-encoding]] and [[positional-encoding|PE]], "
        "see [[self-attention#History]], [[missing-thing]], ![[diagram.png]].\n")
    _write(wiki / "domain" / "articles" / "positional-encoding.md",
        "---\ntitle: Positional Encoding\ntype: article\ncreated: 2026-01-01\n"
        "updated: 2026-01-01\ntags: []\n---\n\nOrder for attention.\n")
    _write(wiki / "sources" / "papers" / "attention-paper.md",
        "---\ntitle: Attention Is All You Need\ntype: source\nsource_type: paper\n"
        "source_path: raw/papers/attention.pdf\ningested: 2026-01-01\ntags: []\n---\n\nThe paper.\n")
    _write(wiki / "README.md",
        "---\ntitle: KB\ntype: index\ngenerated: 2026-01-01\n---\n\nTop index.\n")
    return wiki


def test_build_concept_index_maps_slug_to_path_and_title(tmp_path):
    index = build_concept_index(make_wiki(tmp_path))
    assert index["positional-encoding"].rel_path == "domain/articles/positional-encoding.md"
    assert index["positional-encoding"].title == "Positional Encoding"
    assert index["attention-paper"].type == "source"


def test_rewrite_body_links_to_absolute_markdown_links(tmp_path):
    index = build_concept_index(make_wiki(tmp_path))
    body = "See [[positional-encoding]]."
    out, n, unresolved, linked = rewrite_body_links(body, index)
    assert out == "See [Positional Encoding](/domain/articles/positional-encoding.md)."
    assert n == 1 and unresolved == set() and linked == {"positional-encoding"}


def test_rewrite_body_links_preserves_alias_and_strips_fragment(tmp_path):
    index = build_concept_index(make_wiki(tmp_path))
    out, _, _, _ = rewrite_body_links("[[positional-encoding|PE]] [[self-attention#History]]", index)
    assert "[PE](/domain/articles/positional-encoding.md)" in out
    assert "[Self-Attention](/domain/articles/self-attention.md)" in out


def test_rewrite_body_links_unresolved_degrades_to_text(tmp_path):
    index = build_concept_index(make_wiki(tmp_path))
    out, n, unresolved, _ = rewrite_body_links("[[missing-thing]]", index)
    assert out == "missing-thing"
    assert n == 0 and unresolved == {"missing-thing"}


def test_rewrite_body_links_leaves_asset_embed(tmp_path):
    index = build_concept_index(make_wiki(tmp_path))
    out, _, _, _ = rewrite_body_links("![[diagram.png]]", index)
    assert out == "![[diagram.png]]"


def test_rewrite_frontmatter_refs_to_absolute_paths(tmp_path):
    index = build_concept_index(make_wiki(tmp_path))
    meta = {"sources": ["[[attention-paper]]"], "related": ["[[positional-encoding]]", "[[missing-thing]]"]}
    out, n, unresolved = rewrite_frontmatter_refs(meta, index)
    assert out["sources"] == ["/sources/papers/attention-paper.md"]
    assert out["related"] == ["/domain/articles/positional-encoding.md", "[[missing-thing]]"]
    assert n == 2 and unresolved == {"missing-thing"}


def test_references_section_built_and_dedupes_already_linked(tmp_path):
    index = build_concept_index(make_wiki(tmp_path))
    meta = {"sources": ["[[attention-paper]]"], "related": ["[[positional-encoding]]"]}
    full = references_section(meta, index, set())
    assert "## Sources" in full and "/sources/papers/attention-paper.md" in full
    assert "## Related" in full and "/domain/articles/positional-encoding.md" in full
    # When the related concept is already linked in the body, drop the Related block.
    deduped = references_section(meta, index, {"positional-encoding"})
    assert "## Related" not in deduped and "## Sources" in deduped


def test_export_emits_concept_files_with_nonempty_type(tmp_path):
    wiki = make_wiki(tmp_path)
    result = export_okf(wiki, tmp_path / "okf")
    sa = (tmp_path / "okf" / "domain" / "articles" / "self-attention.md").read_text()
    meta, body = parse_frontmatter(sa)
    assert meta["type"] == "article"
    # body wikilink rewritten, frontmatter refs are absolute paths
    assert "[Positional Encoding](/domain/articles/positional-encoding.md)" in body
    assert meta["sources"] == ["/sources/papers/attention-paper.md"]
    # the source citation surfaces as a body edge
    assert "## Sources" in body
    assert result.files_exported == 4 and result.links_rewritten >= 3
    assert ("domain/articles/self-attention.md", "missing-thing") in result.unresolved


def test_export_generates_root_index_with_okf_version(tmp_path):
    wiki = make_wiki(tmp_path)
    export_okf(wiki, tmp_path / "okf")
    root = (tmp_path / "okf" / "index.md").read_text()
    meta, _ = parse_frontmatter(root)
    assert meta == {"okf_version": OKF_VERSION}


def test_export_dir_index_has_no_frontmatter(tmp_path):
    wiki = make_wiki(tmp_path)
    export_okf(wiki, tmp_path / "okf")
    sub = (tmp_path / "okf" / "domain" / "articles" / "index.md").read_text()
    assert not sub.startswith("---")
    assert "[Positional Encoding](/domain/articles/positional-encoding.md)" in sub


def test_export_does_not_modify_source(tmp_path):
    wiki = make_wiki(tmp_path)
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(wiki.rglob("*.md"))}
    export_okf(wiki, tmp_path / "okf")
    after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(wiki.rglob("*.md"))}
    assert before == after


def test_export_clean_wipes_stale_output(tmp_path):
    wiki = make_wiki(tmp_path)
    out = tmp_path / "okf"
    out.mkdir()
    (out / "stale.md").write_text("old", encoding="utf-8")
    export_okf(wiki, out, clean=True)
    assert not (out / "stale.md").exists()


def test_export_refuses_out_dir_overlapping_wiki(tmp_path):
    wiki = make_wiki(tmp_path)
    for bad_out in (wiki, wiki / "okf", wiki.parent):
        with pytest.raises(ValueError):
            export_okf(wiki, bad_out)
    # the source vault survives every refusal (one-way-projection invariant)
    assert (wiki / "domain" / "articles" / "self-attention.md").is_file()


def test_references_section_skips_heading_already_in_body(tmp_path):
    index = build_concept_index(make_wiki(tmp_path))
    meta = {"sources": ["[[attention-paper]]"]}
    body = "Intro.\n\n## Sources\n\nA hand-written sources section.\n"
    assert references_section(meta, index, set(), body) == ""


def test_note_transclusion_degrades_to_link_without_bang(tmp_path):
    index = build_concept_index(make_wiki(tmp_path))
    out, n, _, _ = rewrite_body_links("![[positional-encoding]]", index)
    assert out == "[Positional Encoding](/domain/articles/positional-encoding.md)"
    assert n == 1 and not out.startswith("!")


def test_link_label_escapes_brackets(tmp_path):
    wiki = make_wiki(tmp_path)
    _write(wiki / "domain" / "articles" / "bracket-title.md",
        "---\ntitle: Section [3.2] Notes\ntype: article\ncreated: 2026-01-01\n"
        "updated: 2026-01-01\ntags: []\n---\n\nBody.\n")
    index = build_concept_index(wiki)
    out, _, _, _ = rewrite_body_links("See [[bracket-title]].", index)
    assert out == "See [Section \\[3.2\\] Notes](/domain/articles/bracket-title.md)."


def test_export_mini_base_is_okf_conformant(tmp_path):
    """End-to-end: the worked example exports to a spec-conformant bundle."""
    out = tmp_path / "okf"
    result = export_okf(MINI_WIKI, out)
    assert result.files_exported > 0 and result.links_rewritten > 0

    for md in sorted(out.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        if md.name == "index.md":
            if md.parent == out:  # bundle root: only okf_version frontmatter allowed
                meta, _ = parse_frontmatter(text)
                assert meta == {"okf_version": OKF_VERSION}
            else:  # non-root index.md: no frontmatter
                assert not text.startswith("---")
        else:  # concept doc: parseable frontmatter with non-empty type
            meta, _ = parse_frontmatter(text)
            assert str(meta.get("type") or "").strip(), f"{md} has empty type"
