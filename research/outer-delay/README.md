# Outer delay

Pure Python, no dependencies. Companion to `outer-momentum`: overlapped DiLoCo-style training applies the outer update `τ` rounds late to hide a sync of cost `C`. On a quadratic the delayed plain outer step is stable iff `αs < 2 sin(π/(4τ+2))`, its best rate is `1 − 2 sin(π/(4τ+2))/κ_H` (exactly `κ_H/(κ_H+1)` at `τ=1`), momentum stops helping as soon as `τ ≥ 1`, and a fully hidden sync gains at most `(τ+1) sin(π/(4τ+2)) ≤ 1` over blocking averaging, so overlap loses to blocking (1.5–4.9× vs plain, 2.3–31× vs tuned momentum) unless the fresh pseudo-gradient carries weight above ½. See `paper/whitepaper.md`.

```bash
cd research/outer-delay
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 13 tests, ~4 s
PYTHONPATH=src python3 experiments/run.py                 # ~1 min; output in experiments/results.txt
```

**Related projects.** [`delayed-outer`](../delayed-outer), written about two hours later and independently, re-derives this project's stability law `αs < 2 sin(π/(4τ+2))` for the same delayed recursion. In both it is the classical stability condition for `x_{t+1} − x_t + c x_{t−τ} = 0` (Levin & May 1976), so the law itself is new in neither. This project adds outer momentum (useless once `τ ≥ 1`), the tuned rate across a curvature spectrum, the wall-clock comparison with blocking averaging, and fresh weight above ½. `delayed-outer` adds gradient noise (the exact delayed noise floor), the single-mode double-root rate and the delay `⌈L/T_c⌉`. The wall-clock verdicts look opposite: here overlap never beats blocking, there it beats no overlap by several times. The comparisons differ, so this is not a contradiction. Here the problem is noiseless and ill-conditioned, the tuned step sits at the stability edge, and the blocking baseline may lengthen `H` to amortise the sync. There `H` is fixed and the step is set by a noise-floor target, small enough that delay is nearly free. Neither project tests the other's baseline.

Noise-free quadratics, shared Hessian, one common delay; MIT.
