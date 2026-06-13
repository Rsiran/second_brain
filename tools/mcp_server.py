"""Knowledge-base MCP server — read-only access to the KB for any MCP client.

Spawned by the client over stdio (Claude Desktop/Code, Hermes Agent, etc.).
Tools wrap the kb-tools modules in-process. Vault root is auto-discovered as
this file's grandparent directory.
"""
from __future__ import annotations
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from tools.search import load_index, build_index, save_index, query as search_query
from tools.search.index import index_is_stale
from tools._common.zones import zone_for_path, slug_for_path
from tools._common.frontmatter import parse_frontmatter, FrontmatterError
from tools.ingest import compute_ingest_diff
from tools.lint import run_lint, Severity


VAULT: Path = Path(__file__).resolve().parent.parent
INDEX_PATH: Path = VAULT / ".search-index" / "index.json"

mcp = FastMCP("kb")

# A slug is a bare kebab-case filename token. This rejects path separators,
# ".." traversal, absolute paths, and glob metacharacters (`*?[]`) — closing
# the only untrusted-input surface on this read-only server. Without it a
# client could escape the articles/sources dirs (e.g. slug="../../out/x/index")
# and read arbitrary frontmatter files outside the KB.
_SLUG_RE = re.compile(r"[a-z0-9._-]+", re.IGNORECASE)


def _is_safe_slug(slug: str) -> bool:
    return isinstance(slug, str) and slug not in ("", ".", "..") and _SLUG_RE.fullmatch(slug) is not None


@mcp.tool()
def get_contract() -> str:
    """Return the KB operating contract and canonical glossary.

    Combines CLAUDE.md (the operating manual + sensitivity rules) and
    CONTEXT.md (the glossary). Call this once at the start of any session
    that touches the KB before using the other tools.
    """
    claude = (VAULT / "CLAUDE.md").read_text(encoding="utf-8")
    context = (VAULT / "CONTEXT.md").read_text(encoding="utf-8")
    return (
        "# CLAUDE.md (KB contract)\n\n"
        f"{claude}\n\n"
        "---\n\n"
        "# CONTEXT.md (canonical glossary)\n\n"
        f"{context}\n"
    )


@mcp.tool()
def search(query: str, limit: int = 10) -> list[dict] | dict:
    """Full-text search over the wiki/.

    Returns a list of hits. Each hit has: slug, title, zone, path, snippet, score.
    If the search index is missing, returns {"error": "index_missing", "remedy": ...}.
    """
    if not INDEX_PATH.exists():
        return {
            "error": "index_missing",
            "remedy": "run `make search-index` in the KB repo",
            "expected_path": str(INDEX_PATH),
        }
    # Rebuild in-memory when the on-disk index has fallen behind the wiki, so
    # the agent never silently searches a stale half of the KB. Best-effort
    # write-back to the (gitignored) cache speeds the next call.
    if index_is_stale(INDEX_PATH, VAULT):
        idx = build_index(VAULT)
        try:
            save_index(idx, str(INDEX_PATH))
        except OSError:
            pass
    else:
        idx = load_index(str(INDEX_PATH))
    hits = search_query(idx, query, limit=limit)
    out: list[dict] = []
    for h in hits:
        path = Path(h.path)
        out.append({
            "slug": slug_for_path(path),
            "title": h.title,
            "zone": zone_for_path(path) or "",
            "path": h.path,
            "snippet": _make_snippet(VAULT / h.path),
            "score": round(h.score, 4),
        })
    return out


def _make_snippet(abs_path: Path, max_chars: int = 240) -> str:
    """Return the first ~240 chars of a markdown file's body, post-frontmatter."""
    try:
        text = abs_path.read_text(encoding="utf-8")
    except OSError:
        return ""
    try:
        _, body = parse_frontmatter(text)
    except FrontmatterError:
        body = text
    body = body.strip()
    if len(body) <= max_chars:
        return body
    return body[:max_chars].rstrip() + "…"


def _find_article_file(slug: str) -> Path | None:
    """Search wiki/<zone>/articles/<slug>.md and wiki/articles/<slug>.md."""
    wiki = VAULT / "wiki"
    if not wiki.is_dir():
        return None
    # Zoned layout (domain/product/market)
    for zone in ("domain", "product", "market"):
        candidate = wiki / zone / "articles" / f"{slug}.md"
        if candidate.is_file():
            return candidate
    # Flat layout (mini-base)
    candidate = wiki / "articles" / f"{slug}.md"
    if candidate.is_file():
        return candidate
    return None


@mcp.tool()
def get_article(slug: str) -> dict:
    """Read a wiki concept article by slug.

    Searches wiki/{domain,product,market}/articles/<slug>.md (zoned layout)
    and wiki/articles/<slug>.md (flat layout). Returns frontmatter, body, and
    the relative path. Returns {"error": "not_found", ...} if no match.
    """
    if not _is_safe_slug(slug):
        return {"error": "invalid_slug", "slug": slug}
    path = _find_article_file(slug)
    if path is None:
        return {
            "error": "not_found",
            "slug": slug,
            "searched": ["domain", "product", "market", "articles"],
        }
    text = path.read_text(encoding="utf-8")
    try:
        meta, body = parse_frontmatter(text)
    except FrontmatterError as e:
        return {"error": "malformed_frontmatter", "slug": slug, "detail": str(e)}
    return {
        "frontmatter": meta,
        "body": body,
        "path": str(path.relative_to(VAULT)),
    }


@mcp.tool()
def get_source(slug: str) -> dict:
    """Read a source summary by slug from wiki/sources/<type>/<slug>.md.

    Searches all source-type subdirectories. Returns frontmatter, body, path.
    Returns {"error": "not_found", ...} if no match.
    """
    if not _is_safe_slug(slug):
        return {"error": "invalid_slug", "slug": slug}
    sources = VAULT / "wiki" / "sources"
    if not sources.is_dir():
        return {"error": "not_found", "slug": slug, "searched": []}
    matches = list(sources.rglob(f"{slug}.md"))
    if not matches:
        searched = sorted(p.name for p in sources.iterdir() if p.is_dir())
        return {"error": "not_found", "slug": slug, "searched": searched}
    path = matches[0]
    text = path.read_text(encoding="utf-8")
    try:
        meta, body = parse_frontmatter(text)
    except FrontmatterError as e:
        return {"error": "malformed_frontmatter", "slug": slug, "detail": str(e)}
    return {
        "frontmatter": meta,
        "body": body,
        "path": str(path.relative_to(VAULT)),
    }


def _index_candidates() -> list[Path]:
    """All index markdown files under wiki/indexes/ and wiki/<zone>/indexes/."""
    wiki = VAULT / "wiki"
    if not wiki.is_dir():
        return []
    out: list[Path] = []
    top = wiki / "indexes"
    if top.is_dir():
        out.extend(sorted(top.glob("*.md")))
    for zone_dir in sorted(p for p in wiki.iterdir() if p.is_dir() and p.name not in ("sources", "indexes", "assets")):
        zoned = zone_dir / "indexes"
        if zoned.is_dir():
            out.extend(sorted(zoned.glob("*.md")))
    return out


def _index_label(path: Path) -> str:
    """The `name` value that resolves to this path. e.g. 'by-topic' or 'domain/key-concepts'."""
    rel = path.relative_to(VAULT / "wiki")
    parts = rel.with_suffix("").parts
    # parts looks like ('indexes','by-topic') or ('domain','indexes','key-concepts')
    if parts[0] == "indexes":
        return parts[-1]
    return f"{parts[0]}/{parts[-1]}"


@mcp.tool()
def list_index(name: str) -> str | dict:
    """Read an index file by name.

    Names: top-level like 'by-topic', 'by-date', 'orphans' (resolves to
    wiki/indexes/<name>.md), or zoned like 'domain/key-concepts' (resolves
    to wiki/domain/indexes/key-concepts.md).
    Returns the body markdown (frontmatter stripped). Returns
    {"error": "not_found", "available": [...]} on miss.
    """
    candidates = _index_candidates()
    by_label = {_index_label(p): p for p in candidates}
    if name not in by_label:
        return {
            "error": "not_found",
            "name": name,
            "available": sorted(by_label.keys()),
        }
    path = by_label[name]
    text = path.read_text(encoding="utf-8")
    try:
        _, body = parse_frontmatter(text)
    except FrontmatterError:
        body = text
    return body


@mcp.tool()
def ingest_status() -> dict:
    """Show pending ingest work — new/modified/orphaned items in raw/ vs wiki/sources/.

    Mirrors `python -m tools.ingest status` as JSON.
    """
    return compute_ingest_diff(VAULT).to_dict()


@mcp.tool()
def lint() -> dict:
    """Run wiki health checks. Mirrors `python -m tools.lint` as JSON.

    Returns {"errors": [...], "warnings": [...]} where each item is
    {"file": "...", "line": int|null, "message": "..."}.
    """
    findings = run_lint(VAULT)
    errors: list[dict] = []
    warnings: list[dict] = []
    for f in findings:
        item = {"file": f.file, "line": f.line, "message": f.message}
        if f.severity == Severity.ERROR:
            errors.append(item)
        else:
            warnings.append(item)
    return {"errors": errors, "warnings": warnings}


def main() -> None:
    """Console-script entry point. Runs the FastMCP app over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
