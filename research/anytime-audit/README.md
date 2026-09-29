# Anytime-valid audits of noisy verification checks

Stdlib-only Python. How many noisy audit checks before slashing, and how to keep auditing until convinced without falsely slashing honest provers. See `paper/whitepaper.md`.

```bash
cd research/anytime-audit
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 8 tests
PYTHONPATH=src python3 experiments/run.py                  # ~10 s; output in experiments/results.txt
```
Results: peeking at a fixed-n test falsely slashes 28% of honest provers at nominal 5%; the mixture e-process stays at 1.6% (Ville bound ≤5%); expected audits match ln(1/δ)/KL with a ½ln n price for not knowing the corruption rate (ratio 1.57→1.25 as δ falls); a tuned SPRT or fixed test planned for the wrong severity misses subtle corruption that the mixture catches. Stylised; MIT.
