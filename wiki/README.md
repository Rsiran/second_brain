---
title: Knowledge Base — Top Index
type: index
generated: 2026-06-13
---

# Knowledge Base

The top-level, cross-zone index of this wiki. See [../CLAUDE.md](../CLAUDE.md) for the full operating contract. This file is the LLM's home page — keep it current as the wiki grows.

## Zones

- **Domain** — the vocabulary and concepts of the subject (the spine). _(empty — fill `domain/articles/` and `domain/indexes/` as sources arrive)_
- **Product** — internal specs, decisions, meetings. _(empty)_
- **Market** — competitors, regulations, standards, external research. _(empty)_

## Cross-zone indexes

- [[by-topic]] — all articles grouped by topical cluster.
- [[by-date]] — all articles by creation date.
- [[orphans]] — sources not yet cited by any article.

## Where to start

- **New contributor?** Read `CLAUDE.md` at the repo root, then `CONTEXT.md`.
- **Want to see a finished example?** Browse `examples/mini-base/` — a tiny, complete KB about transformer architectures.
- **Dropping in a new source?** Put it in the right `raw/<type>/` folder, then run `python -m tools.ingest status`.
- **Looking for something?** Run `python -m tools.search query "..."` or browse [[by-topic]].
