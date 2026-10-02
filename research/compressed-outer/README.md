# Compressed reports in local SGD

Pure Python, no dependencies. Companion to `noisy-local-sgd` and `partial-participation`: DiLoCo-style local SGD whose workers send compressed pseudo-gradients. Exact stationary loss for unbiased multiplicative compression (`α V_w (1+ω)/(M s (2−αsc))`, `c = 1+ω/M`, stable iff `αsc<2`; this re-derives the result of [`compressed-sync`](../compressed-sync)), which contains random participation as `ω = 1/p−1`, and for dithered quantisation (`α (V_w+Δ²/12)/(M s (2−αs))`, stability unchanged), matched to simulation within 0.2–3%; at fixed bandwidth, sparsification favours few full reports while quantisation has an interior optimum near 1.3 bits per coordinate, ~4× below 8-bit reports. See `paper/whitepaper.md`.

```bash
cd research/compressed-outer
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 10 tests, ~5 s
PYTHONPATH=src python3 experiments/run.py                 # output in experiments/results.txt (~4 min)
```

**Related projects.** [`compressed-sync`](../compressed-sync) was written about a quarter of an hour earlier, independently, on the same model. Its coordinate-wise floor `α V_w (1+ω)/(N s ((2−αs) − αsω/N))` and stability limit `αs(1+ω/N) < 2` are the multiplicative result here in different notation, so that part of this project re-derives its result. What this project adds: participation as the same compressor, additive dithered quantisation, and the fixed-bandwidth split between workers and bits. What `compressed-sync` adds: norm-scaled (QSGD-style) compression across modes and the comparison of compressing with syncing less often.

Quadratics, Gaussian noise, independent unbiased compressors; MIT.
