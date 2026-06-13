"""Wiki health checks. Each function returns a list of Findings."""
from __future__ import annotations
from pathlib import Path

from tools._common.slugs import raw_path_to_source_slug
from tools.lint.loader import LoadedBase, LoadedFile
from tools.lint.report import Finding, Severity
from tools.lint.schema import validate_frontmatter


def check_sources_mirror_raw(base: LoadedBase) -> list[Finding]:
    """ERROR if any raw file has no matching wiki/sources/<type>/<slug>.md."""
    findings: list[Finding] = []
    wiki_source_slugs: dict[str, set[str]] = {}  # type_ -> set of slugs present
    for f in base.wiki_files:
        parts = Path(f.relative_path).parts
        if len(parts) >= 4 and parts[0] == "wiki" and parts[1] == "sources":
            type_ = parts[2]
            slug = Path(parts[3]).stem
            wiki_source_slugs.setdefault(type_, set()).add(slug)

    seen: set[tuple[str, str]] = set()
    for raw_rel in base.raw_files:
        expected = raw_path_to_source_slug(raw_rel)
        if expected is None or expected in seen:
            continue
        seen.add(expected)
        type_, slug = expected
        if slug not in wiki_source_slugs.get(type_, set()):
            findings.append(
                Finding(
                    severity=Severity.ERROR,
                    file=raw_rel,
                    message=(
                        f"no matching wiki/sources/{type_}/{slug}.md for this raw file"
                    ),
                )
            )
    return findings


def check_source_paths_exist(base: LoadedBase) -> list[Finding]:
    """ERROR if a wiki/sources/*.md has a source_path that does not exist on disk."""
    findings: list[Finding] = []
    for f in base.wiki_files:
        if f.meta.get("type") != "source":
            continue
        sp = f.meta.get("source_path")
        if not sp:
            continue  # missing source_path is caught by schema check
        target = base.base_dir / sp
        # source_path in the fixtures is already project-relative (e.g. 'tests/fixtures/...'),
        # so also try interpreting it as an absolute project path:
        if not target.exists():
            alt = Path(sp)
            if alt.exists():
                continue
            findings.append(
                Finding(
                    severity=Severity.ERROR,
                    file=f.relative_path,
                    message=f"source_path does not exist: {sp}",
                )
            )
    return findings


def check_frontmatter_schemas(base: LoadedBase) -> list[Finding]:
    """ERROR for any schema violation in any wiki file."""
    findings: list[Finding] = []
    for f in base.wiki_files:
        if f.frontmatter_error is not None:
            findings.append(
                Finding(
                    severity=Severity.ERROR,
                    file=f.relative_path,
                    message=f"frontmatter parse error: {f.frontmatter_error}",
                )
            )
            continue
        errors = validate_frontmatter(f.meta)
        for msg in errors:
            findings.append(
                Finding(severity=Severity.ERROR, file=f.relative_path, message=msg)
            )
    return findings


def _wiki_slugs_index(base: LoadedBase) -> set[str]:
    """All valid link targets: basenames of wiki/*.md files (without extension)."""
    slugs: set[str] = set()
    for f in base.wiki_files:
        slugs.add(Path(f.relative_path).stem)
    return slugs


def check_wikilinks_resolve(base: LoadedBase) -> list[Finding]:
    """ERROR if any wikilink does not resolve to a known wiki file."""
    from tools._common.wikilinks import extract_wikilinks, link_target_slug

    slugs = _wiki_slugs_index(base)
    findings: list[Finding] = []
    for f in base.wiki_files:
        # Also check wikilinks that live inside frontmatter (sources:, related:)
        targets: list[str] = list(f.wikilinks)
        for field in ("sources", "related"):
            for entry in f.meta.get(field, []) or []:
                if isinstance(entry, str):
                    targets.extend(extract_wikilinks(entry))
        for target in targets:
            slug = link_target_slug(target)
            if slug is None:
                continue  # asset embed or empty fragment-only link
            if slug not in slugs:
                findings.append(
                    Finding(
                        severity=Severity.ERROR,
                        file=f.relative_path,
                        message=f"broken wikilink: [[{target}]]",
                    )
                )
    return findings


def check_duplicate_slugs(base: LoadedBase) -> list[Finding]:
    """ERROR if two wiki/*.md files share a slug.

    Slugs are globally unique by contract (CLAUDE.md §3): wikilink resolution
    and MCP article/source lookup both key on the bare stem, so a collision
    silently shadows one of the files.
    """
    by_slug: dict[str, list[str]] = {}
    for f in base.wiki_files:
        if Path(f.relative_path).name in ("README.md",):
            continue  # README.md legitimately repeats across zones
        by_slug.setdefault(Path(f.relative_path).stem, []).append(f.relative_path)

    findings: list[Finding] = []
    for slug, paths in sorted(by_slug.items()):
        if len(paths) > 1:
            others = ", ".join(sorted(paths))
            for p in sorted(paths):
                findings.append(
                    Finding(
                        severity=Severity.ERROR,
                        file=p,
                        message=f"duplicate slug '{slug}' also defined in: {others}",
                    )
                )
    return findings


from datetime import date as _date


def _iter_articles(base: LoadedBase):
    for f in base.wiki_files:
        if f.meta.get("type") == "article":
            yield f


def _iter_sources(base: LoadedBase):
    for f in base.wiki_files:
        if f.meta.get("type") == "source":
            yield f


def check_orphan_sources(base: LoadedBase) -> list[Finding]:
    """WARNING: source has no inbound wikilink from any article."""
    from tools._common.wikilinks import extract_wikilinks, link_target_slug

    cited: set[str] = set()
    for art in _iter_articles(base):
        for target in art.wikilinks:
            slug = link_target_slug(target)
            if slug:
                cited.add(slug)
        for entry in art.meta.get("sources", []) or []:
            if isinstance(entry, str):
                for t in extract_wikilinks(entry):
                    slug = link_target_slug(t)
                    if slug:
                        cited.add(slug)

    findings: list[Finding] = []
    for src in _iter_sources(base):
        slug = Path(src.relative_path).stem
        if slug not in cited:
            findings.append(
                Finding(
                    severity=Severity.WARNING,
                    file=src.relative_path,
                    message=f"orphan source: '{slug}' is not cited by any article",
                )
            )
    return findings


def check_ungrounded_articles(base: LoadedBase) -> list[Finding]:
    """WARNING: article has no entries in its sources: frontmatter."""
    findings: list[Finding] = []
    for art in _iter_articles(base):
        sources = art.meta.get("sources") or []
        if not sources:
            findings.append(
                Finding(
                    severity=Severity.WARNING,
                    file=art.relative_path,
                    message="ungrounded article: sources: frontmatter is empty",
                )
            )
    return findings


def check_dates_sane(base: LoadedBase, today: str | None = None) -> list[Finding]:
    """WARNING: any frontmatter date in the future."""
    if today is None:
        today_d = _date.today()
    else:
        today_d = _date.fromisoformat(today)

    findings: list[Finding] = []
    for f in base.wiki_files:
        for field in ("ingested", "created", "updated", "generated"):
            v = f.meta.get(field)
            if v is None:
                continue
            try:
                d = v if isinstance(v, _date) else _date.fromisoformat(str(v))
            except ValueError:
                continue  # schema check handles invalid format
            if d > today_d:
                findings.append(
                    Finding(
                        severity=Severity.WARNING,
                        file=f.relative_path,
                        message=f"{field}: date in the future: {v}",
                    )
                )
    return findings
