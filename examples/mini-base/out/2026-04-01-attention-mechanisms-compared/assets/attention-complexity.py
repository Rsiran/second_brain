"""Generate a chart comparing attention complexity vs sequence length."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

n = np.arange(64, 4097, 64)
d = 512

# Compute FLOPs (simplified)
dot_product = n ** 2 * d
cross_attn_m256 = n * 256 * d  # fixed encoder length of 256

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(n, dot_product / 1e9, label="Self-attention O(n²d)", linewidth=2)
ax.plot(n, cross_attn_m256 / 1e9, label="Cross-attention O(n·m·d), m=256", linewidth=2, linestyle="--")
ax.set_xlabel("Sequence length (n)")
ax.set_ylabel("FLOPs (billions)")
ax.set_title("Attention Complexity vs Sequence Length (d=512)")
ax.legend()
ax.grid(True, alpha=0.3)
fig.tight_layout()

out_path = Path(__file__).parent / "attention-complexity.png"
fig.savefig(out_path, dpi=150)
print(f"saved {out_path}")
