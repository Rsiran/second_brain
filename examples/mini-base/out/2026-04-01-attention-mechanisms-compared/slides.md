---
marp: true
theme: default
paginate: true
title: Attention Mechanisms Compared
---

# Attention Mechanisms Compared

A comparison of attention variants in transformer architectures.

---

## Scaled Dot-Product Attention

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right) V$$

- Core building block of all transformer attention
- Complexity: O(n² · d)
- Fully parallelizable

---

## Multi-Head Attention

- Runs **h** parallel attention heads on projected subspaces
- Each head: d_k = d_v = d_model / h
- Concatenate outputs, then project

> "Multi-head attention allows the model to jointly attend to information from different representation subspaces." — Vaswani et al.

---

## Complexity at a Glance

| Mechanism | Time | Space |
|-----------|------|-------|
| Dot-product | O(n²d) | O(n²) |
| Multi-head | O(n²d) | O(n²) |
| Cross-attn | O(n·m·d) | O(n·m) |

---

## Scaling with Sequence Length

![Attention complexity](./assets/attention-complexity.png)

The quadratic scaling with sequence length is the main bottleneck for long-context models.

---

## Key Takeaway

All standard attention mechanisms share the **O(n²)** bottleneck. Efficient attention variants (linear attention, sparse attention) are active areas of research.
