from tools.fetch_images.extract import extract_remote_image_urls


def test_extract_markdown_image():
    text = "Here is ![alt text](https://example.com/foo.png)"
    assert extract_remote_image_urls(text) == ["https://example.com/foo.png"]


def test_extract_html_img():
    text = 'Inline <img src="https://cdn.example.com/a.jpg" alt="x"> here'
    assert extract_remote_image_urls(text) == ["https://cdn.example.com/a.jpg"]


def test_ignores_local_paths():
    text = "![local](./img/encoder.png) and ![rel](img/enc.jpg)"
    assert extract_remote_image_urls(text) == []


def test_multiple_urls_deduplicated_preserving_order():
    text = "![a](https://x.com/1.png) ![b](https://x.com/1.png) ![c](https://x.com/2.png)"
    assert extract_remote_image_urls(text) == ["https://x.com/1.png", "https://x.com/2.png"]
