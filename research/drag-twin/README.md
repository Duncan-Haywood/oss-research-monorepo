# Drag twin: what does a linear-drag twin fitted by coast-down get wrong about a quadratic-drag vehicle?

Pure Python, no dependencies. Real vehicle `v' = F − k v²`, twin `v' = F − c v` with `c` calibrated from a coast-down. Results (all from `experiments/results.txt`): (1) the twin stops within `v0/c` = 2.0 while the real vehicle needs 4.6 to reach 0.1·v0 and is logarithmically unbounded (time to 0.01·v0: 19.8 vs 0.92); (2) with secant calibration the steady state is exact at `v_cal` only, and energy per distance is off by exactly `v_cal/v`; (3) the small-signal time constant is 2.001× the real one even at the calibration speed (exactly 2), tangent calibration fixes the time constant but halves the steady-state speed, and no single `c` does both; (4) a speed-hold loop tuned in the twin predicts rise times 1.86×, 1.60×, 1.22× too long at `Kp` = 0.5, 2, 10; (5) fitted `c` depends on the test window (log-speed fit 3.43 → 0.74 as the window grows from 0.2 to 3.0; 20 seeds) and so encodes the protocol, not a physical constant; (6) a fit over speeds [5, 10] is off by 8.0× at speed 1 and 0.54× at 15. Stylised: one dimension, constant `k`, simulated "real" system; see `paper/whitepaper.md`.

```bash
cd research/drag-twin
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 10 tests, under 1 s
PYTHONPATH=src python3 experiments/run.py                 # a few seconds; output in experiments/results.txt
```

**Builds on.** The digital-twin simulation-fidelity and sim-to-real direction of ARPG (<https://arpg.colorado.edu/>), the Autonomous Systems IRT (<https://www.colorado.edu/irt/autonomous-systems/>) and RECUV (<https://www.colorado.edu/recuv/>, UAV and field-robot simulation); no specific paper from those groups is reproduced and nothing here is affiliated with or endorsed by them. Linearisation and identification are classical (Khalil 2002; Ljung 1999; Hoerner 1965). Companion to `uav-energy-twin`, `friction-twin`, `lag-twin` and `saturation-twin` in this repository.

Stylised: simulated "real" system, no field data. MIT.
