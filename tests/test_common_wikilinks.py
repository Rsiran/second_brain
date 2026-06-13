from tools._common.wikilinks import extract_wikilinks, link_target_slug, WIKILINK_RE


def test_extract_simple_link():
    assert extract_wikilinks("See [[transformer]]") == ["transformer"]


def test_extract_multiple_links():
    text = "Read [[attention-is-all-you-need]] and [[self-attention]]."
    assert extract_wikilinks(text) == ["attention-is-all-you-need", "self-attention"]


def test_extract_link_with_display_text():
    # Obsidian supports [[target|display]]; we want the target only
    assert extract_wikilinks("See [[transformer|the Transformer]]") == ["transformer"]


def test_extract_embed_link():
    # ![[asset.png]] is an embed; still a link to 'asset.png'
    assert extract_wikilinks("Here is ![[encoder.png]]") == ["encoder.png"]


def test_no_links():
    assert extract_wikilinks("Plain text without any brackets.") == []


def test_link_target_slug_plain():
    assert link_target_slug("transformer") == "transformer"


def test_link_target_slug_strips_heading_and_block_fragments():
    assert link_target_slug("transformer-architecture#History") == "transformer-architecture"
    assert link_target_slug("self-attention#^block-id") == "self-attention"


def test_link_target_slug_skips_asset_embeds():
    assert link_target_slug("diagram.png") is None
    assert link_target_slug("chart.svg") is None


def test_link_target_slug_handles_md_extension_and_pure_fragment():
    assert link_target_slug("note.md") == "note"
    assert link_target_slug("#in-page-only") is None
