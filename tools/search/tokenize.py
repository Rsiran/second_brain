"""Minimal tokenizer: lowercase, split on non-alphanum, drop stopwords."""
from __future__ import annotations
import re

STOPWORDS = frozenset(
    "a an and are as at be but by for from has have he i in is it its of on "
    "or that the this to was were will with or".split()
)

# Unicode letters and digits, excluding underscore — keeps non-ASCII terms
# (accented and Nordic letters like æ/ø/å) whole instead of fragmenting them
# into junk tokens.
_WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    toks = _WORD_RE.findall(lowered)
    return [t for t in toks if t not in STOPWORDS]
