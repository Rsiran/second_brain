"""Walk a base directory, load all raw/ and wiki/ files, parse wiki frontmatter."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

from tools._common.frontmatter import parse_frontmatter, FrontmatterError
from tools._common.wikilinks import extract_wikilinks


@dataclass
class LoadedFile:
    relative_path: str  # relative to base_dir, POSIX style
    abs_path: Path
    meta: dict
    body: str
    wikilinks: list[str]
    frontmatter_error: str | None = None


@dataclass
class LoadedBase:
    base_dir: Path
    raw_files: list[str] = field(default_factory=list)   # relative POSIX paths
    wiki_files: list[LoadedFile] = field(default_factory=list)


def load_base(base_dir: Path | str) -> LoadedBase:
    base_dir = Path(base_dir)
    loaded = LoadedBase(base_dir=base_dir)

    raw_root = base_dir / "raw"
    if raw_root.is_dir():
        for p in sorted(raw_root.rglob("*")):
            if p.is_file() and p.name != ".gitkeep":
                loaded.raw_files.append(p.relative_to(base_dir).as_posix())

    wiki_root = base_dir / "wiki"
    if wiki_root.is_dir():
        for p in sorted(wiki_root.rglob("*.md")):
            try:
                text = p.read_text(encoding="utf-8")
            except UnicodeDecodeError as e:
                loaded.wiki_files.append(
                    LoadedFile(
                        relative_path=p.relative_to(base_dir).as_posix(),
                        abs_path=p,
                        meta={},
                        body="",
                        wikilinks=[],
                        frontmatter_error=f"cannot decode as UTF-8: {e}",
                    )
                )
                continue

            try:
                meta, body = parse_frontmatter(text)
                err = None
            except FrontmatterError as e:
                meta, body, err = {}, text, str(e)

            loaded.wiki_files.append(
                LoadedFile(
                    relative_path=p.relative_to(base_dir).as_posix(),
                    abs_path=p,
                    meta=meta,
                    body=body,
                    wikilinks=extract_wikilinks(body),
                    frontmatter_error=err,
                )
            )

    return loaded
