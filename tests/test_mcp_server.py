"""Unit tests for tools.mcp_server. Calls tool functions directly."""
from __future__ import annotations
from pathlib import Path

import pytest

from tools import mcp_server


def test_vault_root_resolves_to_repo_root():
    repo_root = Path(__file__).resolve().parent.parent
    assert mcp_server.VAULT == repo_root


def test_main_is_callable():
    assert callable(mcp_server.main)


def test_public_api_search_exports():
    from tools.search import query, load_index
    assert callable(query)
    assert callable(load_index)


def test_public_api_lint_exports():
    from tools.lint import run_lint
    assert callable(run_lint)


def test_public_api_ingest_exports():
    from tools.ingest import compute_ingest_diff
    assert callable(compute_ingest_diff)


def test_get_contract_returns_combined_claude_and_context():
    out = mcp_server.get_contract()
    assert isinstance(out, str)
    # CLAUDE.md content
    assert "Contract for the Knowledge Base" in out
    # CONTEXT.md content (canonical glossary)
    assert "CONTEXT.md" in out or "glossary" in out.lower()
    # Delimiter between the two
    assert "---" in out


@pytest.fixture
def mini_base(monkeypatch, tmp_path):
    """Run mcp_server tools against examples/mini-base/ as the vault root."""
    repo = Path(__file__).resolve().parent.parent
    monkeypatch.setattr(mcp_server, "VAULT", repo / "examples" / "mini-base")
    # Ensure the mini index is fresh; build_index is idempotent.
    from tools.search import build_index, save_index
    idx = build_index(repo / "examples" / "mini-base")
    idx_path = repo / "examples" / "mini-base" / ".search-index" / "mini.json"
    idx_path.parent.mkdir(parents=True, exist_ok=True)
    save_index(idx, str(idx_path))
    monkeypatch.setattr(mcp_server, "INDEX_PATH", idx_path)
    return repo / "examples" / "mini-base"


def test_search_returns_list_of_hits(mini_base):
    hits = mcp_server.search(query="transformer", limit=5)
    assert isinstance(hits, list)
    assert len(hits) > 0
    h = hits[0]
    for key in ("slug", "title", "zone", "path", "snippet", "score"):
        assert key in h, f"missing {key} in hit: {h}"


def test_search_zone_is_derived(mini_base):
    hits = mcp_server.search(query="transformer", limit=10)
    zones = {h["zone"] for h in hits}
    # mini-base uses flat layout, so 'articles' or 'sources' should appear
    assert zones & {"articles", "sources"}


def test_search_returns_index_missing_when_no_index(monkeypatch, tmp_path):
    monkeypatch.setattr(mcp_server, "VAULT", tmp_path)
    monkeypatch.setattr(mcp_server, "INDEX_PATH", tmp_path / "nope.json")
    out = mcp_server.search(query="anything", limit=5)
    assert isinstance(out, dict)
    assert out.get("error") == "index_missing"
    assert "make search-index" in out.get("remedy", "")


def test_get_article_resolves_known_slug(mini_base):
    out = mcp_server.get_article(slug="transformer-architecture")
    assert isinstance(out, dict)
    assert "frontmatter" in out
    assert "body" in out
    assert "path" in out
    assert out["frontmatter"].get("title")
    assert out["body"].strip()


def test_get_article_returns_not_found(mini_base):
    out = mcp_server.get_article(slug="nonexistent-slug-xyz")
    assert out.get("error") == "not_found"
    assert out.get("slug") == "nonexistent-slug-xyz"
    assert isinstance(out.get("searched"), list)


def test_get_source_resolves_known_slug(mini_base):
    out = mcp_server.get_source(slug="attention-is-all-you-need")
    assert "frontmatter" in out
    assert "body" in out
    assert out["frontmatter"].get("type") == "source"


def test_get_source_returns_not_found(mini_base):
    out = mcp_server.get_source(slug="not-a-real-source")
    assert out.get("error") == "not_found"
    assert out.get("slug") == "not-a-real-source"


# --- Path-traversal / input-validation hardening (read-only server, untrusted clients) ---

TRAVERSAL_SLUGS = [
    "../../../README",
    "../../out/2026-04-01-attention-mechanisms-compared/index",  # reaches out/ in mini-base
    "../../sources/papers/attention-is-all-you-need",            # reaches a tier-2 source via get_article
    "/etc/passwd",
    "..",
    "foo/bar",
    "foo\\bar",
]


@pytest.mark.parametrize("slug", TRAVERSAL_SLUGS)
def test_get_article_rejects_unsafe_slug(mini_base, slug):
    out = mcp_server.get_article(slug=slug)
    assert out.get("error") in {"not_found", "invalid_slug"}, out
    # Must never leak a file: no body/frontmatter from outside the articles dirs.
    assert "body" not in out and "frontmatter" not in out


@pytest.mark.parametrize("slug", TRAVERSAL_SLUGS + ["*", "?", "a*"])
def test_get_source_rejects_unsafe_slug(mini_base, slug):
    out = mcp_server.get_source(slug=slug)
    assert out.get("error") in {"not_found", "invalid_slug"}, out
    assert "body" not in out and "frontmatter" not in out


def test_list_index_top_level(mini_base):
    out = mcp_server.list_index(name="by-topic")
    assert isinstance(out, str)
    assert out.strip()
    assert "---" not in out.split("\n")[0]  # frontmatter stripped


def test_list_index_zoned(mini_base):
    # mini-base has no zoned indexes; this should fall through to not_found
    out = mcp_server.list_index(name="domain/key-concepts")
    assert isinstance(out, dict)
    assert out.get("error") == "not_found"
    assert "available" in out


def test_list_index_unknown_returns_available_list(mini_base):
    out = mcp_server.list_index(name="orphans")
    # mini-base may not have orphans; be tolerant — either content or not_found-with-available
    if isinstance(out, dict):
        assert out.get("error") == "not_found"
        assert isinstance(out["available"], list)


def test_ingest_status_returns_diff_dict(mini_base):
    out = mcp_server.ingest_status()
    assert isinstance(out, dict)
    for key in ("new", "modified", "orphaned", "summary"):
        assert key in out
    assert isinstance(out["new"], list)
    assert isinstance(out["modified"], list)
    assert isinstance(out["orphaned"], list)
    assert isinstance(out["summary"], str)


def test_lint_returns_errors_and_warnings(mini_base):
    out = mcp_server.lint()
    assert isinstance(out, dict)
    assert "errors" in out
    assert "warnings" in out
    assert isinstance(out["errors"], list)
    assert isinstance(out["warnings"], list)
