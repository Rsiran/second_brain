from tools.fetch_images.rewrite import rewrite_urls


def test_rewrite_markdown_image():
    text = "![alt](https://example.com/foo.png)"
    out = rewrite_urls(text, {"https://example.com/foo.png": "img/abcdef-foo.png"})
    assert out == "![alt](img/abcdef-foo.png)"


def test_rewrite_preserves_unchanged_text():
    text = "Intro ![a](https://x.com/a.png) middle ![b](./local.png) end"
    out = rewrite_urls(text, {"https://x.com/a.png": "img/x.png"})
    assert out == "Intro ![a](img/x.png) middle ![b](./local.png) end"


def test_rewrite_html_img_tag():
    text = '<img src="https://x.com/a.jpg" alt="a">'
    out = rewrite_urls(text, {"https://x.com/a.jpg": "img/a.jpg"})
    assert 'src="img/a.jpg"' in out
