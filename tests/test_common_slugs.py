from tools._common.slugs import raw_path_to_source_slug


def test_paper_placeholder():
    assert raw_path_to_source_slug("raw/papers/foo.pdf.placeholder") == ("papers", "foo")


def test_article_index():
    assert raw_path_to_source_slug("raw/articles/the-x/index.md") == ("articles", "the-x")


def test_article_image_returns_none():
    assert raw_path_to_source_slug("raw/articles/the-x/img/encoder.png") is None


def test_note():
    assert raw_path_to_source_slug("raw/notes/2026-03-15.md") == ("notes", "2026-03-15")


def test_dataset_readme():
    assert raw_path_to_source_slug("raw/datasets/glue/README.md") == ("datasets", "glue")


def test_image_placeholder():
    assert raw_path_to_source_slug("raw/images/diagram.png.placeholder") == ("images", "diagram")


def test_non_raw_returns_none():
    assert raw_path_to_source_slug("wiki/sources/papers/foo.md") is None


def test_too_short_returns_none():
    assert raw_path_to_source_slug("raw/papers") is None


def test_deep_nested_returns_none():
    assert raw_path_to_source_slug("raw/articles/the-x/data/sub/file.csv") is None


def test_dotfile_returns_none():
    # Stray macOS metadata files must not become bogus sources.
    assert raw_path_to_source_slug("raw/papers/.DS_Store") is None
    assert raw_path_to_source_slug("raw/notes/.gitkeep") is None


def test_dotted_filename_not_truncated():
    # split-at-first-dot would have truncated this to 'yolo-v2'.
    assert raw_path_to_source_slug("raw/papers/yolo-v2.5-survey.pdf") == (
        "papers",
        "yolo-v2.5-survey",
    )
