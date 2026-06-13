"""Tiny hand-rolled inverted index over wiki/*.md files."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import json

from tools._common.frontmatter import parse_frontmatter, FrontmatterError
from tools.search.tokenize import tokenize


@dataclass
class Index:
    base_dir: str
    documents: list[str] = field(default_factory=list)           # doc_id -> relative path
    doc_meta: list[dict] = field(default_factory=list)            # parallel to documents
    postings: dict[str, list[tuple[int, int]]] = field(default_factory=dict)  # token -> [(doc_id, tf)]

    def to_dict(self) -> dict:
        return {
            "base_dir": self.base_dir,
            "documents": self.documents,
            "doc_meta": self.doc_meta,
            "postings": {k: v for k, v in self.postings.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Index":
        idx = cls(base_dir=d["base_dir"])
        idx.documents = d["documents"]
        idx.doc_meta = d["doc_meta"]
        idx.postings = {k: [tuple(x) for x in v] for k, v in d["postings"].items()}
        return idx


def build_index(base_dir: Path | str) -> Index:
    base_dir = Path(base_dir)
    idx = Index(base_dir=str(base_dir))
    wiki_root = base_dir / "wiki"
    if not wiki_root.is_dir():
        return idx

    for p in sorted(wiki_root.rglob("*.md")):
        rel = p.relative_to(base_dir).as_posix()
        # One undecodable file must not abort the whole index build (the lint
        # loader is equally tolerant); flag it but keep going.
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = p.read_text(encoding="utf-8", errors="replace")
        try:
            meta, body = parse_frontmatter(text)
        except FrontmatterError:
            meta, body = {}, text
        title = str(meta.get("title", "")) if isinstance(meta, dict) else ""
        type_ = str(meta.get("type", "")) if isinstance(meta, dict) else ""
        tags = meta.get("tags", []) if isinstance(meta, dict) else []
        tag_text = " ".join(str(t) for t in tags) if isinstance(tags, list) else ""

        full_text = f"{title} {tag_text} {body}"
        tokens = tokenize(full_text)

        doc_id = len(idx.documents)
        idx.documents.append(rel)
        idx.doc_meta.append({"title": title, "type": type_})

        tf: dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        for t, count in tf.items():
            idx.postings.setdefault(t, []).append((doc_id, count))

    return idx


def save_index(idx: Index, path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(idx.to_dict()), encoding="utf-8")


def load_index(path: Path | str) -> Index:
    return Index.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def index_is_stale(index_path: Path | str, base_dir: Path | str) -> bool:
    """True if any wiki/*.md under base_dir is newer than the saved index.

    A stale index silently omits recent ingests from every search result, so
    callers should rebuild (or at least warn) before trusting it.
    """
    index_path = Path(index_path)
    if not index_path.exists():
        return False  # missing is a distinct condition the caller handles
    wiki_root = Path(base_dir) / "wiki"
    if not wiki_root.is_dir():
        return False
    index_mtime = index_path.stat().st_mtime
    newest = max(
        (p.stat().st_mtime for p in wiki_root.rglob("*.md")),
        default=0.0,
    )
    return newest > index_mtime
