"""Validate output bundle structure and frontmatter."""
from __future__ import annotations
import re
from pathlib import Path

from tools._common.frontmatter import parse_frontmatter, FrontmatterError
from tools._common.report import Finding, Severity
from tools.render.schema import validate_output_frontmatter

BUNDLE_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-.+$")


def validate_bundle(bundle_dir: Path, wiki_dir: Path | None = None) -> list[Finding]:
    """Validate an output bundle directory. Returns a list of Findings."""
    findings: list[Finding] = []
    rel = bundle_dir.name

    # Check directory name pattern
    if not BUNDLE_DIR_RE.match(rel):
        findings.append(
            Finding(
                severity=Severity.WARNING,
                file=rel,
                message=f"directory name does not match YYYY-MM-DD-<slug> pattern: {rel}",
            )
        )

    # Check index.md exists
    index_path = bundle_dir / "index.md"
    if not index_path.is_file():
        findings.append(
            Finding(
                severity=Severity.ERROR,
                file=f"{rel}/index.md",
                message="index.md is missing",
            )
        )
        return findings  # can't check further without index.md

    # Parse and validate frontmatter
    try:
        text = index_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        findings.append(
            Finding(
                severity=Severity.ERROR,
                file=f"{rel}/index.md",
                message=f"cannot decode as UTF-8: {e}",
            )
        )
        return findings

    try:
        meta, _body = parse_frontmatter(text)
    except FrontmatterError as e:
        findings.append(
            Finding(
                severity=Severity.ERROR,
                file=f"{rel}/index.md",
                message=f"frontmatter parse error: {e}",
            )
        )
        return findings

    for msg in validate_output_frontmatter(meta):
        findings.append(
            Finding(severity=Severity.ERROR, file=f"{rel}/index.md", message=msg)
        )

    # Check index.html — primary deliverable per CLAUDE.md §3.
    # Warning (not error) because trivial text-only answers may legitimately omit it.
    html_path = bundle_dir / "index.html"
    if not html_path.is_file():
        findings.append(
            Finding(
                severity=Severity.WARNING,
                file=f"{rel}/index.html",
                message="index.html missing — HTML is the default primary deliverable (CLAUDE.md §3); only skip for trivial text-only answers",
            )
        )

    # Check slides.md if present
    slides_path = bundle_dir / "slides.md"
    if slides_path.is_file():
        try:
            slides_text = slides_path.read_text(encoding="utf-8")
            slides_meta, _ = parse_frontmatter(slides_text)
            if not slides_meta.get("marp"):
                findings.append(
                    Finding(
                        severity=Severity.WARNING,
                        file=f"{rel}/slides.md",
                        message="slides.md frontmatter missing 'marp: true'",
                    )
                )
        except (UnicodeDecodeError, FrontmatterError):
            findings.append(
                Finding(
                    severity=Severity.WARNING,
                    file=f"{rel}/slides.md",
                    message="slides.md has no valid frontmatter",
                )
            )

    # Check .py/.png pairing in assets/
    assets_dir = bundle_dir / "assets"
    if assets_dir.is_dir():
        py_files = sorted(assets_dir.glob("*.py"))
        for py_file in py_files:
            stem = py_file.stem
            png = assets_dir / f"{stem}.png"
            placeholder = assets_dir / f"{stem}.png.placeholder"
            if not png.exists() and not placeholder.exists():
                findings.append(
                    Finding(
                        severity=Severity.WARNING,
                        file=f"{rel}/assets/{py_file.name}",
                        message=f"script has no corresponding .png: {stem}.png",
                    )
                )

    # Check sources_consulted wikilinks resolve (warning only)
    if wiki_dir and wiki_dir.is_dir():
        wiki_slugs: set[str] = set()
        for p in wiki_dir.rglob("*.md"):
            wiki_slugs.add(p.stem)

        from tools._common.wikilinks import extract_wikilinks, link_target_slug

        for entry in meta.get("sources_consulted", []) or []:
            if isinstance(entry, str):
                for target in extract_wikilinks(entry):
                    slug = link_target_slug(target)
                    if slug is None:
                        continue
                    if slug not in wiki_slugs:
                        findings.append(
                            Finding(
                                severity=Severity.WARNING,
                                file=f"{rel}/index.md",
                                message=f"sources_consulted wikilink unresolved: [[{target}]]",
                            )
                        )

    return findings


def validate_all_bundles(out_dir: Path, wiki_dir: Path | None = None) -> list[Finding]:
    """Validate all output bundles under out_dir."""
    findings: list[Finding] = []
    if not out_dir.is_dir():
        return findings
    for entry in sorted(out_dir.iterdir()):
        if entry.is_dir() and not entry.name.startswith("."):
            findings.extend(validate_bundle(entry, wiki_dir))
    return findings
