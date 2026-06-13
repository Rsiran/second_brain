"""Query an Index built by tools.search.index."""
from __future__ import annotations
from dataclasses import dataclass

from tools.search.index import Index
from tools.search.tokenize import tokenize


@dataclass
class Hit:
    path: str
    title: str
    type: str
    score: float


def query(idx: Index, q: str, *, type_filter: str | None = None, limit: int = 20) -> list[Hit]:
    terms = tokenize(q)
    if not terms:
        return []

    # Sum term frequencies across query terms (simple TF ranking, good enough at this scale).
    scores: dict[int, float] = {}
    for term in terms:
        for doc_id, tf in idx.postings.get(term, []):
            scores[doc_id] = scores.get(doc_id, 0.0) + tf

    hits: list[Hit] = []
    for doc_id, score in scores.items():
        meta = idx.doc_meta[doc_id]
        if type_filter and meta.get("type") != type_filter:
            continue
        hits.append(
            Hit(
                path=idx.documents[doc_id],
                title=meta.get("title", ""),
                type=meta.get("type", ""),
                score=score,
            )
        )
    hits.sort(key=lambda h: (-h.score, h.path))
    return hits[:limit]
