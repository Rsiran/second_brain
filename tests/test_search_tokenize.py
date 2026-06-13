from tools.search.tokenize import tokenize


def test_tokenize_simple():
    assert tokenize("The Transformer Architecture") == ["transformer", "architecture"]


def test_tokenize_strips_punctuation():
    assert tokenize("Hello, world!") == ["hello", "world"]


def test_tokenize_hyphens_kept_as_words():
    assert tokenize("self-attention mechanism") == ["self", "attention", "mechanism"]


def test_tokenize_dedupes_stopwords():
    toks = tokenize("the a an and or but of in on")
    assert toks == []  # all stopwords


def test_tokenize_keeps_unicode_letters():
    # Non-ASCII letters (accents, Nordic æ/ø/å) must survive tokenization whole.
    assert tokenize("café smørbrød naïve") == [
        "café",
        "smørbrød",
        "naïve",
    ]


def test_tokenize_splits_on_underscore():
    assert tokenize("foo_bar data") == ["foo", "bar", "data"]
