# tools/okf — Open Knowledge Format bridge

Exports the `wiki/` vault as an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) (OKF) bundle so it can be consumed by OKF tooling (e.g. Google's static graph visualizer and Knowledge Catalog) without giving up our Obsidian authoring ergonomics.

It is a **one-way projection** — the wiki stays the source of truth; the exporter never edits the source vault.

## Usage

```bash
# export wiki/ -> out/okf/
uv run python -m tools.okf export

# explicit paths + JSON report
uv run python -m tools.okf export --wiki examples/mini-base/wiki --out /tmp/okf --json
```

`make okf` runs the default export.

## What it does

| Our vault | OKF bundle |
|---|---|
| `[[slug]]` / `[[slug\|alias]]` body wikilinks | `[title](/path/slug.md)` absolute markdown links (graph edges) |
| `sources:` / `related:` frontmatter wikilinks | absolute paths, plus surfaced as body `## Sources` / `## Related` links (edges) |
| every wiki file has a `type` | preserved (defaulted to `concept` if ever missing) |
| `README.md` + named index files | kept as concept docs, **plus** a generated no-frontmatter `index.md` per directory |
| — | bundle-root `index.md` carries `okf_version` |

Unresolved links degrade to plain text (OKF consumers must tolerate broken links) and are reported. Asset embeds (`![[x.png]]`) are left untouched.

## Conformance

The output satisfies OKF v0.1: every non-reserved `.md` has parseable frontmatter with a non-empty `type`; `index.md` files carry no frontmatter except the bundle root (`okf_version`); links are markdown links. See `tools/okf/export.py` for the module docstring.
