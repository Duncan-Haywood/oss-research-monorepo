# Interval elicitation

Stdlib-only Python. Eliciting a drift tolerance interval `[l,u]`: the Winkler interval score is proper for the equal-tailed quantile pair with exact regret `(2/α)[PR(l,α/2)+PR(u,1−α/2)]` (finite even for Cauchy drift) but has unbounded payment; the bounded width-plus-miss loss `(u−l)+λ·1[miss]` elicits the shortest (level-set) interval, 22–31% narrower on lognormal drift, at a 3–48× larger detection sample for α≥0.1. See `paper/whitepaper.md`.

```bash
cd research/interval-elicitation
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 9 tests, <2 s
PYTHONPATH=src python3 experiments/run.py                  # output in experiments/results.txt
```

**Related projects.** [`interval-scores`](../interval-scores) was committed seconds after this project and written independently. It re-derives the Winkler-score half of this one: propriety for the equal-tailed quantile pair, the regret integral, the quadratic shift regret `2f(z)δ²/α`, and finite regret under Cauchy drift whose expected score is infinite. It adds a closed-form Cauchy regret and states the optimal expected score `4sφ(z)/α` explicitly (here it is the value at `λ = 1` of the scale-misreport formula). It also adds the finding that the sign of the misreport asymmetry depends on the level, the rule to score heavy-tailed drift by bounded paired differences, and a comparison with a plain coverage count. The bounded width-plus-miss loss, the shortest interval on skewed drift and the sample cost of a bounded payment are only here.

Risk-neutral verifiers, unimodal drift, one report per task; MIT.
