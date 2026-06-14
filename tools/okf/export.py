"""Export the wiki/ vault as an Open Knowledge Format (OKF) bundle.

OKF (Google Cloud, 2026) is a portable knowledge format: a directory tree of
markdown files with YAML frontmatter, one concept per file, file-path identity,
and a graph of plain-markdown links. Our vault is already OKF-class; the only
divergences are that we (a) link with Obsidian wikilinks ``[[slug]]`` rather
than markdown links and (b) don't ship OKF's reserved ``index.md`` navigation
files or the root ``okf_version`` marker.

This module bridges both. It is a one-way *projection* — the wiki stays the
source of truth — so it never edits the source vault. Per the spec:

- every emitted concept file keeps its frontmatter and carries a non-empty ``type``;
- ``[[slug]]`` body links become absolute bundle-relative links ``[title](/path.md)``;
- ``sources:``/``related:`` frontmatter wikilinks become absolute paths, and any
  not already linked in the body are surfaced as body links (real OKF edges);
- a no-frontmatter ``index.md`` is generated per directory, and the bundle-root
  ``index.md`` carries ``okf_version``.
"""
from __future__ import annotations
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

import yaml

from tools._common.frontmatter import parse_frontmatter, FrontmatterError
from tools._common.wikilinks import link_target_slug
from tools._common.report import Finding, Severity

OKF_VERSION = "0.1"

# OKF reserves these filenames for navigation/history (no concept frontmatter).
RESERVED = {"index.md", "log.md"}

# Inline wikilinks in body text: [[t]], [[t|alias]], [[t#frag]], ![[embed]].
# group(1)=leading '!', group(2)=target (may carry #fragment), group(3)=alias.
_WIKILINK_RE = re.compile(r"(!?)\[\[([^\]|]+?)(?:\|([^\]]*))?\]\]")
# A frontmatter ref value is a bare wikilink string like "[[slug]]".
_FM_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")

_REF_KEYS = ("sources", "related")


def _md_label(text: str) -> str:
    """Escape a string for safe use as CommonMark link text (``[label]``)."""
    return text.replace("[", "\\[").replace("]", "\\]")


@dataclass
class Concept:
    """A wiki file as a resolvable OKF concept."""
    slug: str
    rel_path: str  # POSIX, relative to the wiki/ root == bundle root
    title: str
    type: str


@dataclass
class ExportResult:
    bundle_dir: Path
    files_exported: int = 0
    indexes_generated: int = 0
    links_rewritten: int = 0
    unresolved: list[tuple[str, str]] = field(default_factory=list)  # (file, slug)
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "bundle_dir": str(self.bundle_dir),
            "files_exported": self.files_exported,
            "indexes_generated": self.indexes_generated,
            "links_rewritten": self.links_rewritten,
            "unresolved": [{"file": f, "slug": s} for f, s in self.unresolved],
            "findings": [x.to_dict() for x in self.findings],
        }


def build_concept_index(wiki_dir: Path) -> dict[str, Concept]:
    """Map slug -> Concept for every markdown file under ``wiki_dir``.

    A slug is the filename stem (globally unique by convention; lint enforces
    it). On a duplicate slug the last file wins, mirroring Obsidian.
    """
    index: dict[str, Concept] = {}
    for p in sorted(wiki_dir.rglob("*.md")):
        rel = p.relative_to(wiki_dir).as_posix()
        slug = p.stem
        title, typ = slug, ""
        try:
            meta, _ = parse_frontmatter(p.read_text(encoding="utf-8"))
            title = str(meta.get("title") or slug)
            typ = str(meta.get("type") or "")
        except (FrontmatterError, OSError, UnicodeDecodeError):
            pass
        index[slug] = Concept(slug=slug, rel_path=rel, title=title, type=typ)
    return index


def rewrite_body_links(body: str, index: dict[str, Concept]):
    """Rewrite inline ``[[wikilinks]]`` to OKF absolute markdown links.

    Returns ``(new_body, rewritten_count, unresolved_slugs, linked_slugs)``.
    Unresolved note links degrade to plain display text (no broken edge);
    asset embeds and bare fragments are left untouched.
    """
    rewritten = 0
    unresolved: set[str] = set()
    linked: set[str] = set()

    def repl(m: re.Match) -> str:
        nonlocal rewritten
        target, alias = m.group(2).strip(), m.group(3)
        disp = alias.strip() if (alias and alias.strip()) else None
        slug = link_target_slug(target)
        if slug is None:
            return m.group(0)  # asset embed (e.g. ![[x.png]]) or fragment-only
        concept = index.get(slug)
        if concept is None:
            unresolved.add(slug)
            return disp or target  # plain text — tolerated broken link
        rewritten += 1
        linked.add(slug)
        # Note transclusions (![[note]]) have no OKF/markdown equivalent, so we
        # deliberately project them to a plain link — the leading '!' (group 1)
        # is dropped. Asset embeds (![[x.png]]) never reach here (slug is None).
        return f"[{_md_label(disp or concept.title or slug)}](/{concept.rel_path})"

    return _WIKILINK_RE.sub(repl, body), rewritten, unresolved, linked


def rewrite_frontmatter_refs(meta: dict, index: dict[str, Concept]):
    """Rewrite ``sources:``/``related:`` wikilink strings to absolute paths.

    Returns ``(new_meta, rewritten_count, unresolved_slugs)``. Unresolved
    entries are left verbatim so no information is lost.
    """
    new_meta = dict(meta)
    rewritten = 0
    unresolved: set[str] = set()
    for key in _REF_KEYS:
        vals = new_meta.get(key)
        if not isinstance(vals, list):
            continue
        out: list = []
        for v in vals:
            slug = _ref_slug(v)
            if slug is not None:
                concept = index.get(slug)
                if concept is not None:
                    out.append(f"/{concept.rel_path}")
                    rewritten += 1
                    continue
                unresolved.add(slug)
            out.append(v)
        new_meta[key] = out
    return new_meta, rewritten, unresolved


def _ref_slug(value) -> str | None:
    """Slug from a frontmatter ref value like ``"[[slug#frag|alias]]"``."""
    if not isinstance(value, str):
        return None
    m = _FM_WIKILINK_RE.search(value)
    return link_target_slug(m.group(1)) if m else None


def references_section(
    meta: dict, index: dict[str, Concept], already_linked: set[str], body: str = ""
) -> str:
    """Build ``## Sources`` / ``## Related`` body sections as OKF edges.

    Only includes resolved refs not already linked from the prose body, so the
    relationship becomes a graph edge without duplicating in-body citations.
    Skips a heading the ``body`` already defines, so a hand-authored section is
    never duplicated. Mutates ``already_linked`` to dedupe across the two sections.
    """
    blocks: list[str] = []
    for key, heading in (("sources", "Sources"), ("related", "Related")):
        vals = meta.get(key)
        if not isinstance(vals, list):
            continue
        if re.search(rf"^#+\s+{heading}\b", body, re.MULTILINE | re.IGNORECASE):
            continue  # the prose body already has this section; don't duplicate it
        items: list[str] = []
        for v in vals:
            slug = _ref_slug(v)
            if slug is None or slug in already_linked:
                continue
            concept = index.get(slug)
            if concept is None:
                continue
            items.append(f"* [{_md_label(concept.title or slug)}](/{concept.rel_path})")
            already_linked.add(slug)
        if items:
            blocks.append(f"## {heading}\n\n" + "\n".join(items))
    return "\n\n".join(blocks)


def render_concept(meta: dict, body: str) -> str:
    """Serialize ``(meta, body)`` back to a frontmatter markdown document."""
    fm = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, default_flow_style=False).strip()
    return f"---\n{fm}\n---\n\n{body.rstrip()}\n"


def export_okf(wiki_dir: Path | str, out_dir: Path | str, clean: bool = True) -> ExportResult:
    """Export ``wiki_dir`` as an OKF bundle at ``out_dir``. Never edits the source."""
    wiki_dir = Path(wiki_dir)
    out_dir = Path(out_dir)
    if not wiki_dir.is_dir():
        raise NotADirectoryError(f"wiki directory not found: {wiki_dir}")

    # The export is a one-way projection: it must never touch the source vault.
    # Reject an out_dir that equals, contains, or is contained by wiki_dir —
    # otherwise clean=True would rmtree the vault and a re-export would re-ingest
    # its own bundle. (The default out/okf is safely outside wiki/.)
    wiki_resolved, out_resolved = wiki_dir.resolve(), out_dir.resolve()
    if (
        out_resolved == wiki_resolved
        or wiki_resolved in out_resolved.parents
        or out_resolved in wiki_resolved.parents
    ):
        raise ValueError(
            f"output directory {out_dir} overlaps the source vault {wiki_dir}; "
            "choose an --out path outside the wiki tree"
        )

    index = build_concept_index(wiki_dir)
    if clean and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    result = ExportResult(bundle_dir=out_dir)
    emitted: list[str] = []

    for p in sorted(wiki_dir.rglob("*.md")):
        rel = p.relative_to(wiki_dir).as_posix()
        if PurePosixPath(rel).name in RESERVED:
            result.findings.append(
                Finding(Severity.WARNING, rel, "source uses an OKF-reserved filename; skipped")
            )
            continue
        try:
            meta, body = parse_frontmatter(p.read_text(encoding="utf-8"))
        except (FrontmatterError, OSError, UnicodeDecodeError) as e:
            result.findings.append(Finding(Severity.WARNING, rel, f"skipped (no parseable frontmatter): {e}"))
            continue

        if not str(meta.get("type") or "").strip():
            meta = {**meta, "type": "concept"}
            result.findings.append(Finding(Severity.WARNING, rel, "missing 'type'; defaulted to 'concept'"))

        new_body, n_body, unresolved, linked = rewrite_body_links(body, index)
        result.links_rewritten += n_body
        result.unresolved.extend((rel, s) for s in sorted(unresolved))

        refs = references_section(meta, index, set(linked), new_body)
        new_meta, n_fm, unresolved_fm = rewrite_frontmatter_refs(meta, index)
        result.links_rewritten += n_fm
        result.unresolved.extend((rel, s) for s in sorted(unresolved_fm))

        out_body = new_body.rstrip()
        if refs:
            out_body = f"{out_body}\n\n{refs}" if out_body else refs

        dest = out_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render_concept(new_meta, out_body), encoding="utf-8")
        emitted.append(rel)
        result.files_exported += 1

    result.indexes_generated = _generate_indexes(out_dir, emitted, index)
    return result


def _generate_indexes(bundle_dir: Path, emitted: list[str], index: dict[str, Concept]) -> int:
    """Write a navigation ``index.md`` per directory (root carries okf_version)."""
    dirs: dict[str, dict] = {".": {"concepts": [], "subdirs": set()}}
    for rel in emitted:
        parent = PurePosixPath(rel).parent.as_posix()
        dirs.setdefault(parent, {"concepts": [], "subdirs": set()})["concepts"].append(rel)
    # Walk every directory's ancestor chain so intermediate dirs get an index too.
    for d in list(dirs.keys()):
        cur = PurePosixPath(d)
        while cur.as_posix() != ".":
            parent = cur.parent.as_posix()
            entry = dirs.setdefault(parent, {"concepts": [], "subdirs": set()})
            entry["subdirs"].add(cur.as_posix())
            cur = cur.parent

    count = 0
    for d, info in dirs.items():
        is_root = d == "."
        title = "Knowledge Base" if is_root else _dir_title(d)
        lines: list[str] = [f"# {title}", ""]
        for sub in sorted(info["subdirs"]):
            lines.append(f"* [{_dir_title(sub)}/](/{sub}/index.md)")
        if info["subdirs"] and info["concepts"]:
            lines.append("")
        for rel in sorted(info["concepts"]):
            concept = index.get(PurePosixPath(rel).stem)
            label = concept.title if concept else PurePosixPath(rel).stem
            suffix = f" — {concept.type}" if concept and concept.type else ""
            lines.append(f"* [{_md_label(label)}](/{rel}){suffix}")
        body = "\n".join(lines).rstrip() + "\n"
        if is_root:
            body = f"---\nokf_version: '{OKF_VERSION}'\n---\n\n{body}"
        target = bundle_dir if is_root else bundle_dir / d
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.md").write_text(body, encoding="utf-8")
        count += 1
    return count


def _dir_title(posix_dir: str) -> str:
    """Human label for a directory path: ``domain/articles`` -> ``Articles``."""
    name = posix_dir.rstrip("/").split("/")[-1]
    return name.replace("-", " ").replace("_", " ").title()
