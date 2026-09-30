# Backlash twin: what does gear play, which a linear twin lacks, do to a tracking loop?

Pure Python, no dependencies. Sibling of `research/deadband-twin` and `research/deadband-noise-twin` (deadband: no motion below a command threshold); backlash is different: the load rests inside the play and *state* (which side the gears last touched) decides whether it moves. Motor `m⁺ = m + K(r − x)` integrates the tracking error; the load `x` is coupled through play of half-width `d`. The reference is a square wave `±A/2` with half-period `P`. K=0.5, d=0.1, P=10 unless stated. The linear twin (`x = m`) has exact swing `(A/2)(1−ρ)/(1+ρ)`, `ρ=(1−K)^P`, and an exact rms error; both match simulation to 6 digits.

Results (all from `experiments/results.txt`):
- **Exact moving limit cycle.** Each half-period the load is stuck for `n = ⌈2d/(K(A/2+a))⌉` steps, then follows the motor; the swing `a` solves a linear equation given `n`. Predicted swings and rms errors match simulation to all printed digits (e.g. A=0.1: n=5, swing 0.0484, real rms error 0.0721 vs twin 0.0365, **1.98×**; A=0.2: 1.58×; A=0.5: 1.25×; A=1: 1.11×). The twin's optimism is largest for small references and fades for large ones.
- **A load that never moves.** If the motor excursion `KPA/2 ≤ 2d` (here A ≤ 0.08) the load can stay at rest and the rms error is exactly `A/2` (0.0250 at A=0.05 vs twin 0.0182, 1.37×; the twin's error is smaller at every amplitude tested). For A ≤ 0.06 in this run, moving cycles do not exist at all; other initial gaps gave irregular partial motion or rest.
- **Bistability.** For A = 0.065–0.075 the same loop has a moving cycle (swing 0.0257–0.0339) *or* rests (swing 0) depending only on the initial gap `g0` (g0=−d: rests; other g0: moves). A twin cannot represent this; which branch a physical robot is on depends on its history.
- **Longer half-periods hurt more.** The rest threshold is `A_s = 4d/(KP)`; just below it the rest error is `A_s/2` and the real/twin error ratio is 1.0, 1.4, 1.9, 2.7 for P = 5, 10, 20, 40.

```bash
cd research/backlash-twin
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 6 tests, <1 s
PYTHONPATH=src python3 experiments/run.py                 # <1 s; output in experiments/results.txt
```

**Builds on.** The digital-twin simulation-fidelity and sim-to-real direction of ARPG (<https://arpg.colorado.edu/>), the Autonomous Systems IRT (<https://www.colorado.edu/irt/autonomous-systems/>) and HIRO Group (<https://hiro-group.ronc.one/>, manipulation actuators); no specific paper from those groups is reproduced and nothing here is affiliated with or endorsed by them. The backlash operator and describing-function analysis of backlash are classical (Nordin & Gutman 2002; Tao & Kokotović 1996). Companion to `deadband-twin`, `deadband-noise-twin`, `control-twin`, `saturation-twin` in this repository.

Stylised: scalar integral servo, symmetric play, known `d`, square-wave reference, a simulated "real" system, no field data and no noise. Only symmetric cycles (and the rest state at x=0) are derived; the asymmetric partial-motion outcomes at small A are observed, not characterised. Which cycle is stable when two exist is inferred from simulation, not proved. MIT.
