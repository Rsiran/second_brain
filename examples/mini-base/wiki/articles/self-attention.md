---
title: Self-Attention
type: article
created: 2026-03-10
updated: 2026-03-10
tags: [ml, attention, transformer]
sources:
  - "[[attention-is-all-you-need]]"
  - "[[the-illustrated-transformer]]"
related:
  - "[[transformer-architecture]]"
---

# Self-Attention

Self-attention is the core mechanism of the [[transformer-architecture]]. Each token computes queries (Q), keys (K), and values (V) as linear projections of its input embedding, then attends to every other token in the sequence via scaled dot-product attention: `softmax(QK^T / sqrt(d_k)) V`.

Multi-head self-attention runs this in parallel across several learned projection subspaces and concatenates the results, letting the model attend to different types of relationships simultaneously.

See [[attention-is-all-you-need]] for the formal definition and [[the-illustrated-transformer]] for the visual intuition.
