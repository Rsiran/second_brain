---
title: Transformer Architecture
type: article
created: 2026-03-10
updated: 2026-03-15
tags: [ml, architecture, transformer]
sources:
  - "[[attention-is-all-you-need]]"
  - "[[the-illustrated-transformer]]"
  - "[[2026-03-15-meeting]]"
  - "[[glue-benchmark]]"
  - "[[transformer-diagram]]"
related:
  - "[[self-attention]]"
  - "[[positional-encoding]]"
---

# Transformer Architecture

The transformer is a sequence-to-sequence architecture introduced in [[attention-is-all-you-need]] that replaces recurrence with [[self-attention]]. It consists of a stack of identical encoders and a stack of identical decoders.

## Encoder

Each encoder layer has two sub-layers: a multi-head [[self-attention]] block and a position-wise feed-forward network, each wrapped in a residual connection and layer norm.

## Decoder

Each decoder layer has three sub-layers: masked multi-head self-attention (so tokens cannot attend to future positions), encoder-decoder attention (over the encoder's output), and a feed-forward network.

## Positional information

Because self-attention is permutation-invariant, the architecture injects order information via [[positional-encoding]] added to the input embeddings.

See [[the-illustrated-transformer]] for a visual walkthrough.
