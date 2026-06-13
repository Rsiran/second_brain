from tools._common.frontmatter import parse_frontmatter, FrontmatterError
import pytest


def test_parse_frontmatter_valid():
    text = """---
title: Hello
type: article
tags: [ml, test]
---

Body text here.
"""
    meta, body = parse_frontmatter(text)
    assert meta == {"title": "Hello", "type": "article", "tags": ["ml", "test"]}
    assert body.strip() == "Body text here."


def test_parse_frontmatter_missing_raises():
    with pytest.raises(FrontmatterError):
        parse_frontmatter("No frontmatter here, just text.")


def test_parse_frontmatter_unclosed_raises():
    with pytest.raises(FrontmatterError):
        parse_frontmatter("---\ntitle: x\nno closing delimiter\n")


def test_parse_frontmatter_empty_body_ok():
    meta, body = parse_frontmatter("---\ntitle: x\ntype: index\n---\n")
    assert meta["title"] == "x"
    assert body == ""


def test_parse_frontmatter_invalid_yaml_raises():
    with pytest.raises(FrontmatterError):
        parse_frontmatter("---\ntitle: [unterminated\n---\n\nbody\n")


def test_parse_frontmatter_non_mapping_raises():
    # A YAML list (or scalar) is valid YAML but not a frontmatter mapping.
    with pytest.raises(FrontmatterError):
        parse_frontmatter("---\n- just\n- a\n- list\n---\n\nbody\n")


def test_parse_frontmatter_tolerates_utf8_bom():
    meta, body = parse_frontmatter("\ufeff---\ntitle: x\ntype: index\n---\n\nbody\n")
    assert meta["title"] == "x"
    assert body.strip() == "body"
