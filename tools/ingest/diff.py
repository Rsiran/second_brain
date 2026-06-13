"""Compute the diff between raw/ and wiki/sources/ to find pending ingest work."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from tools._common.frontmatter import parse_frontmatter, FrontmatterError
from tools._common.slugs import raw_path_to_source_slug


@dataclass
class NewItem:
    raw_path: str
    raw_type: str  # directory name: articles, papers, notes, etc.
    slug: str


@dataclass
class ModifiedItem:
    raw_path: str
    raw_type: str
    slug: str
    source_path: str
    ingested: str


@dataclass
class OrphanedItem:
    source_path: str
    missing_raw: str


@dataclass
class IngestDiff:
    new: list[NewItem] = field(default_factory=list)
    modified: list[ModifiedItem] = field(default_factory=list)
    orphaned: list[OrphanedItem] = field(default_factory=list)

    @property
    def summary(self) -> str:
        return f"{len(self.new)} new, {len(self.modified)} modified, {len(self.orphaned)} orphaned"

    @property
    def total(self) -> int:
        return len(self.new) + len(self.modified) + len(self.orphaned)

    def to_dict(self) -> dict:
        return {
            "new": [
                {"raw_path": i.raw_path, "raw_type": i.raw_type, "slug": i.slug}
                for i in self.new
            ],
            "modified": [
                {
                    "raw_path": i.raw_path,
                    "raw_type": i.raw_type,
                    "slug": i.slug,
                    "source_path": i.source_path,
                    "ingested": i.ingested,
                }
                for i in self.modified
            ],
            "orphaned": [
                {"source_path": i.source_path, "missing_raw": i.missing_raw}
                for i in self.orphaned
            ],
            "summary": self.summary,
        }


def _load_source_index(wiki_dir: Path) -> dict[tuple[str, str], tuple[str, dict]]:
    """Map (source_type, slug) -> (relative_source_path, frontmatter) for all wiki/sources/ files."""
    index: dict[tuple[str, str], tuple[str, dict]] = {}
    sources_dir = wiki_dir / "sources"
    if not sources_dir.is_dir():
        return index
    for p in sorted(sources_dir.rglob("*.md")):
        rel = p.relative_to(wiki_dir.parent)
        parts = rel.parts
        if len(parts) < 4:
            continue  # e.g. wiki/sources/.gitkeep
        type_ = parts[2]  # wiki/sources/<type>/<slug>.md
        slug = p.stem
        try:
            text = p.read_text(encoding="utf-8")
            meta, _ = parse_frontmatter(text)
        except (UnicodeDecodeError, FrontmatterError):
            meta = {}
        index[(type_, slug)] = (rel.as_posix(), meta)
    return index


def compute_ingest_diff(base_dir: Path | str) -> IngestDiff:
    """Compute the diff between raw/ and wiki/sources/."""
    base_dir = Path(base_dir)
    diff = IngestDiff()

    raw_dir = base_dir / "raw"
    wiki_dir = base_dir / "wiki"

    # Collect all raw slugs
    raw_slugs: dict[tuple[str, str], str] = {}  # (type, slug) -> raw_path
    if raw_dir.is_dir():
        for p in sorted(raw_dir.rglob("*")):
            if p.is_file() and p.name != ".gitkeep":
                rel = p.relative_to(base_dir).as_posix()
                result = raw_path_to_source_slug(rel)
                if result is not None and result not in raw_slugs:
                    raw_slugs[result] = rel

    # Load wiki/sources index
    source_index = _load_source_index(wiki_dir)

    # Find new and modified
    for (type_, slug), raw_path in sorted(raw_slugs.items()):
        if (type_, slug) not in source_index:
            diff.new.append(NewItem(raw_path=raw_path, raw_type=type_, slug=slug))
        else:
            source_path, meta = source_index[(type_, slug)]
            ingested = meta.get("ingested")
            if ingested is not None:
                # Compare raw file mtime with ingested date. If the comparison
                # can't be made (unstat-able file, unparseable ingested date),
                # fail safe: report it as modified rather than silently dropping
                # it, so the drift surfaces instead of hiding.
                raw_file = base_dir / raw_path
                try:
                    mtime = raw_file.stat().st_mtime
                    mtime_date = date.fromtimestamp(mtime)
                    ingested_date = (
                        ingested
                        if isinstance(ingested, date)
                        else date.fromisoformat(str(ingested))
                    )
                    needs_review = mtime_date > ingested_date
                except (OSError, ValueError):
                    needs_review = True
                if needs_review:
                    diff.modified.append(
                        ModifiedItem(
                            raw_path=raw_path,
                            raw_type=type_,
                            slug=slug,
                            source_path=source_path,
                            ingested=str(ingested),
                        )
                    )

    # Find orphaned sources. A source is only orphaned when neither its
    # location-derived raw path nor its declared source_path resolves to a real
    # file — sources distilled from a shared note (e.g. a reading list) point at
    # that note via source_path and must not be reported as orphans.
    for (type_, slug), (source_path, meta) in sorted(source_index.items()):
        if (type_, slug) in raw_slugs:
            continue
        sp = meta.get("source_path")
        if sp and (base_dir / sp).exists():
            continue
        diff.orphaned.append(
            OrphanedItem(
                source_path=source_path,
                missing_raw=sp or f"raw/{type_}/{slug}",
            )
        )

    return diff
