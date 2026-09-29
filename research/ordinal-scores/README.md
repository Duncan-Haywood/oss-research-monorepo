# Ordinal scores

Stdlib-only Python. Ordinal follow-up to `categorical-scores`: when the K outcome classes are ordered (binned drift magnitude), the ranked probability score `Σ_k (R_k−1[y≤k])²` has exact regret `Σ_k (R_k−P_k)²`, is the sum of binary Brier scores over every tolerance threshold, and its incentive to move mass a distance `d` is `d` times the adjacent-bin incentive (Brier: flat). A translated misreport costs RPS linearly in the shift `s` (0.5, 1.5, 2.5, …) but Brier saturates; weighting one threshold prices one tolerance decision with regret `≤ 2√(excess)` (sharp). See `paper/whitepaper.md`.

```bash
cd research/ordinal-scores
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 7 tests, <1 s
PYTHONPATH=src python3 experiments/run.py                  # output in experiments/results.txt
```
Risk-neutral verifiers, one report per task; MIT.
