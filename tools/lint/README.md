# tools/lint

Health-check a knowledge base against the `CLAUDE.md` contract.

## Usage

```bash
python -m tools.lint [PATH]        # default PATH is '.'
python -m tools.lint --json        # machine-readable output for LLMs
```

Exits non-zero if any ERROR-level finding is reported.

## Checks

**ERROR:**
- every `raw/` file has a matching `wiki/sources/` summary
- every `wiki/sources/*.md` has a `source_path` pointing to an existing file
- every `wiki/*.md` has valid frontmatter per the schemas in `tools/lint/schema.py`
- every wikilink resolves to an existing wiki file

**WARNING:**
- orphan sources (no inbound link from any article)
- ungrounded articles (empty `sources:` frontmatter)
- dates in the future

## Invocation from an LLM

Use `--json` to parse the output programmatically. Fix ERROR findings before declaring ingest or query work done.
