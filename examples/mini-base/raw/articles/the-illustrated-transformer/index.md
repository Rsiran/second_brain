---
title: The Illustrated Transformer
source_url: https://jalammar.github.io/illustrated-transformer/
author: Jay Alammar
clipped: 2026-03-10
---

# The Illustrated Transformer

In the previous post, we looked at Attention — a ubiquitous method in modern deep learning models. Attention is a concept that helped improve the performance of neural machine translation applications. In this post, we will look at The Transformer — a model that uses attention to boost the speed with which these models can be trained.

## A High-Level Look

Let's begin by looking at the model as a single black box. In a machine translation application, it would take a sentence in one language, and output its translation in another.

![encoder](./img/encoder.png)

The encoding component is a stack of encoders. The decoding component is a stack of decoders of the same number.

Each encoder has two sub-layers: a self-attention layer and a feed-forward neural network. The decoder has both of these, plus an attention layer in between that helps the decoder focus on relevant parts of the input sentence.
