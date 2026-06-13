---
title: Positional Encoding
type: article
created: 2026-03-10
updated: 2026-03-15
tags: [ml, transformer]
sources:
  - "[[attention-is-all-you-need]]"
  - "[[2026-03-15-meeting]]"
related:
  - "[[transformer-architecture]]"
  - "[[self-attention]]"
---

# Positional Encoding

The [[transformer-architecture]]'s [[self-attention]] mechanism is permutation-invariant: it has no built-in notion of token order. Positional encoding fixes this by injecting position information into the input.

The original [[attention-is-all-you-need]] uses fixed sinusoidal encodings at different frequencies, **added** (not concatenated) to the token embeddings. This lets the model learn to attend by relative position.

Later variants include learned positional embeddings, rotary positional embeddings (RoPE), and ALiBi.
