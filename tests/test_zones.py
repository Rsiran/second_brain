"""Tests for tools._common.zones."""
from __future__ import annotations
from pathlib import Path

import pytest

from tools._common.zones import zone_for_path, slug_for_path


@pytest.mark.parametrize("rel,expected", [
    ("wiki/domain/articles/self-attention.md", "domain"),
    ("wiki/product/articles/some-spec.md", "product"),
    ("wiki/market/articles/competitor-x.md", "market"),
    ("wiki/sources/papers/foo.md", "sources"),
    ("wiki/indexes/by-topic.md", "indexes"),
    ("wiki/articles/transformer-architecture.md", "articles"),  # flat layout (mini-base)
    ("wiki/README.md", "wiki"),
])
def test_zone_for_path(rel, expected):
    assert zone_for_path(Path(rel)) == expected


def test_zone_for_path_outside_wiki_returns_none():
    assert zone_for_path(Path("raw/articles/foo.md")) is None


def test_slug_for_path():
    assert slug_for_path(Path("wiki/domain/articles/self-attention.md")) == "self-attention"
    assert slug_for_path(Path("wiki/sources/papers/attention-is-all-you-need.md")) == "attention-is-all-you-need"
