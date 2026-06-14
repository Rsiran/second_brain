# CLAUDE.md — Contract for the Knowledge Base

Read this first, every session. This file is the operating manual for this repository. It tells you (the LLM) how the KB is structured, what you own, what you must never do, and how to do your job.

## 1. Purpose, scope, and sensitivity

This is an **LLM-managed knowledge base**. A human drops source material into `raw/`; you (the LLM) compile it into a navigable, well-linked wiki under `wiki/`, then answer questions as file bundles in `out/`. The repo is an Obsidian vault and ships a small set of Python tools for ingest, lint, search, and rendering.

The wiki is organized into **three zones**:

- **Domain** (`wiki/domain/`) — the vocabulary and concepts of the subject area. Stable, slow-changing. The spine that the other two zones cite.
- **Product & internal** (`wiki/product/`) — your organization's own material: specs, decisions, meetings, internal reasoning.
- **Market & external** (`wiki/market/`) — the outside world: competitors, regulations, standards, news, market and competitive intelligence, and external research.

> The three zones are a sensible default, not a hard requirement. A single-zone KB also works — see `examples/mini-base/`, which uses a flat `wiki/articles/`. The tools support both layouts. If you change the zone set, update `VALID_ZONES` in `tools/lint/schema.py` and this file **together**.

### Sensitivity policy

> **Customize this section for your situation.** The default below is deliberately generic. Tighten it for regulated, classified, export-controlled, or contractually-restricted domains; relax it for a fully public KB.

Default stance:

- ✅ **Public information** — papers, news, public regulations, vendor websites.
- ✅ **Confidential internal** — unreleased specs, pricing, partner conversations, meeting notes. **Private repo only.**
- ❌ **Anything you are not legally or contractually allowed to store here** — classified or formally-marked material, export-controlled technology, NDA-bound content that mandates a specific approved store, or regulated personal data.

**If in doubt, do not ingest. Ask a human.**

#### Stub pattern for restricted references

If a wiki article needs to reference restricted content you cannot store here, create a **stub article** that names the concept and points to where the real content lives, without reproducing it:

```markdown
---
title: <Concept> (STUB)
type: article
created: 2026-06-13
updated: 2026-06-13
tags: [restricted, stub]
sources: []
related: ["[[some-related-concept]]"]
---

**Restricted content.** The real material lives in <access-controlled
location>. Do NOT reproduce it here. This stub exists only so other
articles can wikilink to the concept.
```

Mental model: **you (the LLM) own `wiki/` and `out/`. The human owns `raw/`.** Your job is to keep `wiki/` a faithful, navigable, well-linked index of everything in `raw/`.

## 2. Directory map

```
CLAUDE.md          This file. The contract.
README.md          Human-facing: how to use this KB.
CONTEXT.md         Canonical glossary — short definitions, aliases, conflicts.
Makefile           make lint | make ingest-status | make search-index | make test
pyproject.toml
.obsidian/         Vault config (pre-set; graph scoped to wiki/).
.gitignore
raw/               Source documents. Append-only. You NEVER edit these.
  articles/          Web-clipped articles (one folder per article, with img/).
  papers/            Academic / whitepapers (PDFs, placeholders).
  repos/             Code repositories (cloned or referenced).
  datasets/          Datasets.
  images/            Standalone images.
  notes/             Your own notes: learning, reading, thoughts.
  specs/             Internal product / engineering specs.
  meetings/          Meeting notes.
  competitors/       Per-company competitor profiles and intel.
  regulations/       Regulatory texts (laws, directives, agency rules).
  standards/         Industry / technical standards and reference protocols.
  datasheets/        Hardware / component datasheets.
  incidents/         Real-world events and case studies.
  books/             Full-length books and handbooks (textbooks, monographs, reference encyclopedias).
wiki/              Compiled wiki. YOU own this.
  README.md          Top-level cross-zone index.
  sources/           1:1 mirror of raw/. One summary file per raw doc, grouped by raw type.
  domain/            Ontology zone (the spine).
    articles/          Concept articles you synthesize.
    indexes/           Domain-scoped indexes.
  product/           Internal zone.
    articles/
    indexes/
  market/            External research zone.
    articles/
    indexes/
  indexes/           Cross-zone rollups (by-topic, by-date, orphans).
  assets/            Images the wiki owns (diagrams, curated figures).
out/               Query outputs (gitignored). You write answers here as file bundles.
tools/             CLIs you call as subroutines. See §5.
tests/             Tool self-tests. You don't usually touch these.
examples/mini-base/  Reference implementation (a tiny transformers KB, single-zone).
                     Read it if unsure how a file type should look.
```

### Raw type → default zone mapping

The zone an article lands in is usually obvious from the source type:

| Source type  | Default zone    | Notes |
|--------------|-----------------|-------|
| articles     | market          | Generic web articles; unless clearly about internal work |
| papers       | domain / market | Research papers → domain; market reports → market |
| repos        | market / domain | Yours may be internal — beware what you ingest |
| datasets     | domain          | |
| images       | any             | Per context |
| notes        | any             | Per context |
| specs        | product         | Always internal |
| meetings     | product         | Always internal |
| competitors  | market          | Always |
| regulations  | market          | Always |
| standards    | domain / market | Technical/reference standards → domain; procurement → market |
| datasheets   | domain          | Generic component specs; internal versions go in specs/ |
| incidents    | market          | Public incidents here; internal post-mortems go in meetings/ |
| books        | domain / market | Default domain (foundational); market when about industry/competitors |

If a source spans multiple zones, pick the primary zone for the concept article and tag with the others.

## 3. File-format rules

Every file in `wiki/` has YAML frontmatter. Filenames are **kebab-case** slugs. Internal links are **Obsidian wikilinks** `[[slug]]`, never relative markdown links. Four schemas:

### Source summary — `wiki/sources/<type>/<slug>.md`

```yaml
---
title: <original title>
type: source
source_type: article | paper | repo | dataset | image | note | spec | meeting | competitor | regulation | standard | datasheet | incident | book
source_path: raw/<type>/<slug>[/index.md]
source_url: https://...            # optional, only if from web
authors: [name1, name2]             # optional
ingested: YYYY-MM-DD                # required
extraction: full-text | abstract-only | reference-only | snapshot-YYYY-MM-DD   # how much of the source we actually captured
tags: [tag1, tag2]
---
```

Body: a concise summary (100–400 words), key claims, and cross-references to `[[wiki/...]]`.

**`extraction:` values** — signal to future readers how much to trust the summary:
- `full-text` — had the complete paper/doc; summary is grounded in the actual content.
- `abstract-only` — had only abstract + metadata (paywalled paper, incomplete clip); summary reflects that.
- `reference-only` — title, authors, URL, maybe a sentence from the landing page. Use as a citation anchor; don't trust synthesis against this.
- `snapshot-YYYY-MM-DD` — for volatile pages (vendor marketing, news) clipped on the given date. Content on the live URL may have drifted.

### Concept article — `wiki/<zone>/articles/<slug>.md`

Zone ∈ {`domain`, `product`, `market`} (or none, for a flat single-zone KB). Slugs are globally unique across zones — `[[self-attention]]` resolves regardless of where it lives.

```yaml
---
title: <concept title>
type: article
zone: domain | product | market   # optional; advisory metadata
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2]
sources:
  - "[[some-source-summary]]"
related:
  - "[[some-related-concept]]"
---
```

Body: the synthesized explanation. **Cite `wiki/sources/` via wikilinks**, never `raw/` directly.

The `zone:` field is advisory metadata — the file's physical location is the source of truth.

### Index — `wiki/<zone>/indexes/<name>.md`, `wiki/indexes/<name>.md`, and `wiki/README.md`

```yaml
---
title: Index — <...>
type: index
generated: YYYY-MM-DD
---
```

Body: grouped wikilinks with brief annotations.

### Output — `out/YYYY-MM-DD-<slug>/`

A bundle of files. The primary deliverable is **`index.html`** — a rich HTML document with embedded CSS, SVG diagrams, charts, tables, and any interactivity the answer benefits from. This is the artifact you share with stakeholders; open it in a browser to verify before reporting done.

`index.md` lives alongside it as the **metadata anchor**: it carries the YAML frontmatter (below) and a short prose summary describing what the bundle contains. The lint and search tools read `index.md`, so the metadata and summary stay queryable. Wiki references in the summary use wikilinks.

```yaml
---
title: <answer title>
type: output
query: "<the original question>"
created: YYYY-MM-DD
format: report | slides | chart | mixed
sources_consulted:
  - "[[slug1]]"
  - "[[slug2]]"
tags: [tag1, tag2]
filed_back: false
filed_back_as: ""
---
```

Output bundles may also contain `slides.md` (Marp), `assets/*.py` (matplotlib), and `assets/*.png` (rendered charts referenced by `index.html`).

For trivial text-only answers where HTML adds no visible value, you may skip `index.html` and put the answer body directly in `index.md`. HTML is the default; markdown-only is the exception.

## 4. Workflows

### 4.1 Ingest (user added files to `raw/`)

0. Run `python -m tools.ingest status` to see what needs processing.
1. **Sensitivity check first.** For each new raw doc, confirm it is allowed under §1. If not, remove it from `raw/` and reference it by stub. Note any confidential-internal status in the source summary (`tags: [confidential]`).
2. Write or update `wiki/sources/<type>/<slug>.md`.
3. Decide the article zone using the table in §2. Identify concepts the new source touches.
4. For each concept, update or create `wiki/<zone>/articles/<concept>.md`; add the new source to its `sources:` frontmatter.
5. Update `wiki/<zone>/indexes/*` (zone-scoped) and `wiki/indexes/{by-topic,by-date,orphans}.md` (cross-zone).
6. Update `wiki/README.md` if the top-level picture changed.
7. If a new canonical term was introduced or an existing one sharpened, update `CONTEXT.md`.
8. Run `make search-index` to refresh the search index over the new content.
9. Run `make lint` and fix all errors before stopping.

#### Source-type guidance

| Type | Summary guidance |
|---|---|
| article | Summarize main argument; note key claims; reference co-located images. |
| paper | Title, authors, abstract, key contributions. Note if full text unreadable. |
| repo | Purpose, stack, key APIs, relation to KB topic. |
| dataset | Schema, size, provenance, what questions it answers. |
| image | Description, source attribution, concept illustrated. |
| note | Preserve key points. Link to mentioned sources/concepts. |
| spec | **Internal.** What system/component, functional vs non-functional requirements, decisions referenced (ADRs). |
| meeting | **Internal.** Attendees, date, decisions made, action items, open questions. |
| competitor | Company, product, tech stack, funding, customers (if public), positioning vs. you. |
| regulation | Jurisdiction, scope, enforcement body, relevance. |
| standard | Issuing body, scope, current revision, relevance. |
| datasheet | Manufacturer, part, key specs, applicability. |
| incident | Date, location, actors, outcome, what it teaches. |
| book | Author(s), publisher, edition, ISBN. For monographs: chapter-by-chapter or thematic synthesis. For multi-author reference handbooks (>500 pp): list the full ToC, then summarise only the in-scope chapters. Tag `extraction: full-text` only for chapters actually read; the whole-book entry stays `abstract-only` until every relevant chapter is summarised. |

#### Concept article creation heuristic

- If 2+ sources discuss the same concept and no article exists, create one.
- If only 1 source mentions a concept, note it in the source summary but don't create a standalone article yet.
- **Exception for `domain` zone seed stubs** (hand-created ontology placeholders). These may start empty; fill them as sources arrive.
- When creating an article, check `wiki/indexes/by-topic.md` to avoid near-duplicate slugs.

### 4.2 Query (user asked a question)

#### Research phase

1. Read `wiki/README.md` and `wiki/indexes/by-topic.md` to orient.
2. Use `python -m tools.search query "..."` to find relevant articles and sources.
3. Follow wikilinks. Read enough to answer fully.
4. If the wiki is insufficient, say so — do not fabricate. Suggest what raw material might help.

#### Output phase

5. Create `out/YYYY-MM-DD-<slug>/`.
6. Write **`index.html`** as the primary deliverable: rich layout, embedded CSS / SVG / charts where they help, structured to be read once by a stakeholder. Open it in a browser to verify.
7. Write `index.md` with the output frontmatter schema (§3) and a short prose summary describing the bundle. Choose the `format:` value (report / slides / chart / mixed).
8. All wiki references in `index.md` use wikilinks.
9. **Do not reply only in chat.** The bundle is the deliverable. (Trivial text-only answer? Skip `index.html` and put the answer in `index.md`.)

#### File-back phase

10. Evaluate: reusable, grounded, non-duplicate?
11. If yes, create or update `wiki/<zone>/articles/<slug>.md`, adapting the output into wiki style.
12. Copy charts to `wiki/assets/`. Update indexes and backlinks.
13. Set `filed_back: true` and `filed_back_as: "<slug>"` in the output frontmatter.
14. Run `make lint`.

### 4.3 Health check

1. Run `make lint`.
2. Fix broken links, fill missing frontmatter, summarize orphan sources, propose new article candidates for clusters.

## 5. Tool reference

Run these through `uv run` (e.g. `uv run python -m tools.lint`) or after activating the venv (`source .venv/bin/activate`). The `make` targets already wrap them in `uv run`.

| Tool | Invocation | What it does |
|------|------------|--------------|
| ingest | `python -m tools.ingest status` | Shows new/modified/orphaned raw files. |
| search | `python -m tools.search query "..."` | Full-text search over `wiki/`. |
| lint | `python -m tools.lint` | Health-checks `wiki/` against the schemas. |
| render | `python -m tools.render validate <dir>` | Validates an output bundle. `marp <dir>` converts slides to HTML. |
| fetch-images | `python -m tools.fetch_images <path>` | Downloads remote images in a raw markdown file to local. |
| okf | `python -m tools.okf export` | Exports `wiki/` as an Open Knowledge Format bundle (`out/okf/`) for OKF tooling. One-way projection; never edits the vault. See `tools/okf/README.md`. |
| mcp-server | `python -m tools.mcp_server` (stdio) | Read-only MCP server (`kb-mcp`) for Claude, Hermes Agent, and other MCP clients. See `docs/mcp-integration.md`. |

## 6. Anti-patterns — do not do these

- Do **not** edit files in `raw/`. If a source is wrong, note it in the `wiki/sources/` summary.
- Do **not** cite `raw/` directly from `wiki/` articles. Cite `wiki/sources/` instead.
- Do **not** create wiki files without frontmatter.
- Do **not** fabricate dates. Use the current system date.
- Do **not** use relative markdown links inside `wiki/`. Use wikilinks.
- Do **not** batch-rewrite many wiki files in one pass unless announced first.
- Do **not** skip `make lint` at the end of an ingest or query workflow.
- Do **not** ingest content above the sensitivity ceiling (§1). Stub it and move on.
- Do **not** invent internal facts. If a claim needs an internal source, ask the human; don't fill it in from outside knowledge.
- Do **not** treat `examples/mini-base/` as real content. It's a reference implementation for tool behaviour and is about transformer architectures.

## 7. About `CONTEXT.md`

`CONTEXT.md` at the repo root is the canonical glossary — short definitions, aliases, conflict resolutions. It overlaps with the ontology articles in `wiki/domain/articles/` but serves a different purpose:

- `CONTEXT.md` — **one line per term**, canonical name, aliases to avoid, flagged ambiguities. Read-at-a-glance.
- `wiki/domain/articles/<slug>.md` — **full concept article** with body, cited sources, related concepts.

When you learn a new canonical term or resolve an ambiguity, update `CONTEXT.md` inline in that session. Don't batch.
