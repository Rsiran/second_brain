# raw/ — Source Documents

Append-only. You drop things here; the LLM ingests them into `wiki/`. **Never edit files in `raw/` after ingest.** If a source is wrong, correct it in the corresponding `wiki/sources/` summary.

## Source types

| Folder | Contents | Typical zone |
|---|---|---|
| `articles/` | Web-clipped articles (one folder per article, with `index.md` and `img/`). | market |
| `papers/` | Academic / whitepapers. PDFs or `.placeholder` stubs. | domain / market |
| `repos/` | Code repositories (cloned or referenced). | market / domain |
| `datasets/` | Datasets (folder with README). | domain |
| `images/` | Standalone images. | any |
| `notes/` | Your own notes: learning, reading, thoughts. | any |
| `specs/` | **Internal.** Product / engineering specs. | product |
| `meetings/` | **Internal.** Meeting notes. | product |
| `competitors/` | Per-company competitor profiles. | market |
| `regulations/` | Regulatory texts (laws, directives, agency rules). | market |
| `standards/` | Industry / technical standards and reference protocols. | domain / market |
| `datasheets/` | Hardware / component datasheets. | domain |
| `incidents/` | Real-world events and case studies. | market |
| `books/` | Full-length books and handbooks (textbooks, monographs, reference encyclopedias). | domain / market |

## Where does X go? — the routing rule

The types above are a mix of **medium** (article, paper, note, book) and **subject** (competitor, regulation, standard, incident, datasheet, spec, meeting). That creates ambiguity for things like "a web article about a competitor" — which folder?

**Rule: subject wins when a subject folder fits.**

If the item is inherently *about* one of the subjects with a dedicated folder, put it there regardless of medium. Medium folders (`articles/`, `papers/`, `notes/`, `books/`) are for items where the medium *is* the content — generic research not about a specific entity.

### Routing table

| What it is | Goes in | Why |
|---|---|---|
| Web article announcing a competitor's product | `raw/competitors/<company>/` | Subject = the competitor |
| Whitepaper *from* a competitor describing their tech | `raw/competitors/<company>/` | Subject = the competitor |
| A law, directive, or agency rule | `raw/regulations/` | Subject = regulation |
| An industry or technical standard | `raw/standards/` | Subject = standard |
| News article about a notable event | `raw/incidents/<slug>/` | Subject = incident |
| Hardware / component datasheet | `raw/datasheets/` | Subject = the hardware |
| Research paper on a general method (not about a company) | `raw/papers/` | No subject folder fits; medium wins |
| Blog post on theory in general | `raw/articles/<slug>/` | Generic research |
| Your own reading notes or learning log | `raw/notes/` | Your journal |
| An internal spec | `raw/specs/<slug>/` | Always subject |
| Meeting notes | `raw/meetings/<slug>.md` | Always subject |
| A dataset | `raw/datasets/<slug>/` | Subject = the data |
| Code repository | `raw/repos/<slug>/` | Subject = the repo |

**Edge case: the item genuinely fits two subjects.** Pick the dominant axis; add the secondary as a tag in the wiki summary during ingest (e.g. `tags: [competitor, pricing]`). Don't duplicate the raw file.

## Naming: folder vs. file

Two valid shapes per source. Pick based on whether you expect to accumulate related items.

**Folder with `index.md`** — when you expect multiple items or images:

```
raw/competitors/acme/
  index.md                          ← your running profile / canonical doc
  2026-03-15-product-launch.md      ← one clipping
  2026-04-02-blog-post.md           ← another clipping
  img/                              ← associated images
raw/articles/the-illustrated-transformer/
  index.md
  img/encoder.png
```

**Single `.md` or `.pdf`** — for one-off items:

```
raw/regulations/eu-2021-821.pdf
raw/papers/vaswani-2017-attention.pdf
raw/notes/2026-04-19-reading-log.md
raw/meetings/2026-04-20-partner-call.md
```

The ingest tool treats both as one source. For a folder, the slug is the folder name; for a file, the filename stem. Slugs are **kebab-case** and unique within a type.

### Conventions

- **Dates in slugs** for things that are events or point-in-time: `2026-04-20-partner-call`, `2024-heathrow-sighting`.
- **Entity name for profiles**: `acme`, `globex`, `initech-model-7`.
- **Descriptive kebab-case for everything else**: `vaswani-2017-attention`, `eu-2021-821`, `iso-27001`.

## Sensitivity — read before dropping anything in

Respect the KB's sensitivity ceiling. By default: public material and confidential-internal (private repo only) are fine; anything you are not legally or contractually allowed to store here is **not**. If in doubt, do not drop it in — ask.

See [../CLAUDE.md §1](../CLAUDE.md) for the full policy and the stub pattern for restricted references.

## After dropping

Run `make ingest-status` to see what the LLM should pick up next.
