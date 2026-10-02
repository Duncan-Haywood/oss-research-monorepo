# Interval scores

Stdlib-only Python. Paying verifiers for a central (1−α) drift interval with the Winkler interval score `(u−l)+(2/α)(l−y)₊+(2/α)(y−u)₊`: strictly proper for the α/2 and 1−α/2 quantiles, regret splits into two one-sided cdf integrals with a closed form (normal and Cauchy), the optimal expected score is exactly `4sφ(z)/α`, scale misreports cost a level-dependent asymmetric amount, and under Cauchy drift the scores have no mean but paired score differences are bounded, so detection still works. See `paper/whitepaper.md`.

```bash
cd research/interval-scores
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 7 tests, ~1 s
PYTHONPATH=src python3 experiments/run.py                  # output in experiments/results.txt
```

**Related projects.** Most of this re-derives the result of [`interval-elicitation`](../interval-elicitation), committed seconds earlier and written independently. That project already has the propriety of the Winkler score, its regret integral, the shift regret, finite regret under Cauchy drift, and a scale-misreport formula whose value at the honest report is `4sφ(z)/α`. What this project adds: a closed-form Cauchy regret, the level-dependent sign of the misreport asymmetry, paired score differences as the rule for heavy-tailed drift, and detection by score compared with detection by coverage count. `interval-elicitation` also covers the bounded width-plus-miss loss, the shortest interval on skewed drift and the sample cost of a bounded payment, which are not here.

Risk-neutral verifiers, known location family, one interval per task; MIT.
