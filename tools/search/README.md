# tools/search

Tiny full-text search over `wiki/`. Hand-rolled inverted index, no external search deps.

## Usage

```bash
# Build (or rebuild) the index
python -m tools.search index --base .

# Query
python -m tools.search query "self attention"
python -m tools.search query "transformer" --type article --limit 5

# Web UI (optional)
python -m tools.search serve --port 8080
```

The index is written to `.search-index/index.json` by default (gitignored).

## For LLM agents

Use `query` to find candidate files before reading them. Grep is still useful for exact strings; search is for semantic-ish queries over tokenized text.
