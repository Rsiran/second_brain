---
title: Attention Is All You Need
type: source
source_type: paper
source_path: examples/mini-base/raw/papers/attention-is-all-you-need.pdf.placeholder
source_url: https://arxiv.org/abs/1706.03762
authors: [Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin]
ingested: 2026-03-10
tags: [ml, architecture, transformer, seminal]
---

# Attention Is All You Need

The 2017 paper that introduced the [[transformer-architecture]]. Replaces recurrence and convolutions with [[self-attention]] as the core mechanism for sequence modeling.

## Key claims

- Self-attention scales better than RNNs for long-range dependencies because every position attends to every other in O(1) sequential steps.
- Multi-head attention lets the model jointly attend to information from different representation subspaces.
- [[positional-encoding]] is added to input embeddings because self-attention is permutation-invariant.
- Achieves state-of-the-art BLEU on WMT 2014 English-to-German translation with significantly less training compute than prior work.
