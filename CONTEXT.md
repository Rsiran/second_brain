# CONTEXT — Canonical Glossary

The canonical vocabulary for this knowledge base. **One line per term.** For full concept articles with bodies and citations, see `wiki/domain/articles/`.

This file is opinionated: when multiple words exist for the same concept, pick the canonical one and list the others as aliases to avoid. The LLM reads this at a glance to keep naming consistent across the wiki.

> **This is a template.** Replace the example entries below with your own domain's vocabulary as you ingest sources. Update it inline whenever you learn a new canonical term or resolve an ambiguity — don't batch.

## Format

Each entry is a bolded canonical term, a one-line definition, and an optional `_Avoid_:` line listing aliases not to use and why. Link related terms with wikilinks (`[[other-term]]`), which resolve to `wiki/domain/articles/<slug>.md`.

```markdown
**Canonical Term**:
A one-sentence definition. Link to [[related-term]] where useful.
_Avoid_: alias-one (why), alias-two (why).
```

## Example entries

These come from the worked example in `examples/mini-base/` (transformer architectures). Delete them once your own glossary exists.

**Self-attention**:
A mechanism where each token in a sequence attends to every other token, weighting them by learned query–key similarity to build context-aware representations.
_Avoid_: intra-attention (older term for the same thing), self-alignment (ambiguous).

**Positional encoding**:
A scheme for injecting token-order information into an otherwise order-agnostic [[self-attention]] model, either fixed (sinusoidal) or learned.
_Avoid_: position embedding (fine, but pick one and stay consistent), order encoding (non-standard).

**Transformer architecture**:
A sequence-to-sequence neural architecture built from stacked [[self-attention]] and feed-forward blocks, with [[positional-encoding]] supplying order.
_Avoid_: "attention model" (too broad — attention predates transformers).
