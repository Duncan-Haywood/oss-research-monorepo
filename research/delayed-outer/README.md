# Delayed outer

Pure Python, no dependencies. Companion to `outer-momentum` and `local-sgd-bias`: what if the DiLoCo-style outer step is applied `τ` rounds late so a synchronisation of latency `C` hides behind compute (overlapped / streaming sync)? On a quadratic the stale outer step is `x_{t+1} = x_t − a·x_{t−τ}` with `a = α·s`, whose stability limit is exactly `a < 2 sin(π/(4τ+2)) ≈ π/(2τ)` (so plain averaging, `α = 1`, marginal at `τ = 1` and divergent for `τ ≥ 2`), and whose fastest single mode has radius `τ/(τ+1)`. The step-size cap exactly cancels the throughput gained: `(τ+1)·2 sin(π/(4τ+2))` is 2 at `τ = 0, 1` and falls to `π/2`, so naive overlap never beats blocking sync in a grid search over `(H, τ)` (up to 1.25× slower), while a curvature-based delay compensation with estimate ratio `λ ∈ [0.75, 1]` recovers the delay-free rate and hides the latency completely (2–17× faster when `C` is large), with overestimates (`λ > 1`) tightening the cap. See `paper/whitepaper.md`.

```bash
cd research/delayed-outer
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 11 tests, ~8 s
PYTHONPATH=src python3 experiments/run.py                 # ~3 min; output in experiments/results.txt
```
Noise-free quadratics, shared Hessian, curvature known or secant-estimated exactly; MIT.
