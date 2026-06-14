.PHONY: help lint lint-self lint-example search-index ingest-status okf test clean

help:
	@echo "make lint          # lint the knowledge base and examples/mini-base"
	@echo "make ingest-status # show new/modified/orphaned raw files"
	@echo "make search-index  # build search index over wiki/"
	@echo "make okf           # export wiki/ as an OKF bundle to out/okf/"
	@echo "make test          # run pytest + lint"
	@echo "make clean         # remove generated artifacts"

lint: lint-self lint-example

lint-self:
	uv run python -m tools.lint .

lint-example:
	uv run python -m tools.lint examples/mini-base

ingest-status:
	uv run python -m tools.ingest status

search-index:
	uv run python -m tools.search index --base . --index .search-index/index.json

okf:
	uv run python -m tools.okf export

test: lint
	uv run python -m tools.search index --base examples/mini-base --index .search-index/mini.json
	uv run python -m tools.render validate examples/mini-base/out/2026-04-01-attention-mechanisms-compared
	uv run --extra dev python -m pytest tests/ -q
	@echo "OK — knowledge base smoke test passed"

clean:
	rm -rf .search-index .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
