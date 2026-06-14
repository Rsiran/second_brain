# Knowledge Base

An **LLM-managed knowledge base** template. Drop sources into `raw/`, ask an LLM (Claude Code, Hermes Agent, etc.) to ingest them, and it compiles a navigable, well-linked wiki under `wiki/` and answers questions as shareable file bundles under `out/`. Browse it as an [Obsidian](https://obsidian.md) vault; query it through a small, tested set of Python tools.

Three wiki zones:

- **Domain** — the vocabulary and concepts of your subject (the stable spine).
- **Product** — your own internal specs, decisions, and meetings.
- **Market** — the outside world: competitors, regulations, standards, external research.

See [CLAUDE.md](./CLAUDE.md) for the full operating contract and [CONTEXT.md](./CONTEXT.md) for the canonical glossary.

## Quick start

**Prerequisites:** [uv](https://docs.astral.sh/uv/), `make`, and Python 3.11+. (`uv` creates and manages the virtualenv for you.)

```bash
# install tools (creates .venv and installs kb-tools + dev deps)
uv venv
uv pip install -e ".[dev]"

# health-check
make lint

# show pending ingest work
make ingest-status

# build search index
make search-index

# smoke test (lint + render + pytest)
make test
```

The `make` targets wrap every command in `uv run`, so they work on a fresh clone with no manual venv activation. To call the tools directly, either prefix with `uv run` (e.g. `uv run python -m tools.search query "..."`) or activate the venv first (`source .venv/bin/activate`).

## How it works

1. **Drop sources into `raw/`.** One folder per source type: `articles/`, `papers/`, `notes/`, `specs/`, `meetings/`, `competitors/`, `regulations/`, `standards/`, `datasheets/`, `incidents/`, `repos/`, `datasets/`, `images/`, `books/`. See [raw/README.md](./raw/README.md) for the routing rule.
2. **Ask the LLM to ingest.** It reads [CLAUDE.md](./CLAUDE.md), walks `raw/`, writes a summary for each source in `wiki/sources/<type>/`, and synthesizes or updates concept articles in `wiki/{domain,product,market}/articles/`. Run `make lint` to verify.
3. **Ask questions.** The LLM searches `wiki/` and writes answers to `out/YYYY-MM-DD-<slug>/` as a rich `index.html` bundle. Valuable answers get filed back into `wiki/`.
4. **Browse in Obsidian.** The repo root is the vault root; the graph view is scoped to `wiki/`.

## Worked example

`examples/mini-base/` is a tiny, complete reference KB (topic: transformer architectures) that exercises every file type and passes the same lint as the main repo. Read it when you're unsure how a source summary, concept article, index, or output bundle should look. `make test` lints and renders it.

## Adapting this template to your domain

This repo is generic on purpose. To specialize it:

1. **Set the topic.** Rewrite [CONTEXT.md](./CONTEXT.md) with your canonical glossary and `wiki/README.md` / `wiki/domain/indexes/` with your ontology seeds.
2. **Tune the sensitivity policy.** Edit §1 of [CLAUDE.md](./CLAUDE.md) to match what you're allowed to store (the default is conservative and generic).
3. **Adjust the zones (optional).** The `domain`/`product`/`market` split is a default. For a single-topic KB, use a flat `wiki/articles/` like the mini-base. If you change the zone set, update `VALID_ZONES` in `tools/lint/schema.py` and CLAUDE.md §1 together.
4. **Adjust the source types (optional).** Add or remove types in `VALID_SOURCE_TYPES` in `tools/lint/schema.py`, mirrored by folders in `raw/` and `wiki/sources/` and the tables in CLAUDE.md §2 and raw/README.md.

## Tools

| Tool | Invocation | What it does |
|------|------------|--------------|
| ingest | `python -m tools.ingest status` | New/modified/orphaned raw files. |
| search | `python -m tools.search query "..."` | Full-text search over `wiki/`. |
| lint | `python -m tools.lint` | Schema + link health check. |
| render | `python -m tools.render validate <dir>` | Validate / render an output bundle. |
| fetch-images | `python -m tools.fetch_images <path>` | Localize remote images in a raw markdown file. |
| okf | `python -m tools.okf export` | Export `wiki/` as an Open Knowledge Format bundle. |
| mcp-server | `python -m tools.mcp_server` | Read-only MCP server (`kb-mcp`). |

## MCP integration

The repo ships an MCP server (`kb-mcp`) exposing seven read-only tools — search, article/source reads, index reads, ingest status, lint — to any MCP client (Claude Desktop/Code, Hermes Agent, …). See [docs/mcp-integration.md](./docs/mcp-integration.md) for setup.

## Interoperability — Open Knowledge Format

`make okf` (or `python -m tools.okf export`) projects `wiki/` into an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) (OKF) bundle in `out/okf/` — Obsidian wikilinks become absolute markdown links, and each directory gets a navigation `index.md`. This makes the vault consumable by OKF tooling (e.g. graph visualizers, Google's Knowledge Catalog) while we keep authoring in Obsidian. The export is one-way and never edits the vault. See [tools/okf/README.md](./tools/okf/README.md).

## Layout

See [CLAUDE.md §2](./CLAUDE.md) for the full directory map. The short version: `raw/` (you own, append-only) → `wiki/` (the LLM owns, compiled) → `out/` (query answers, gitignored).
