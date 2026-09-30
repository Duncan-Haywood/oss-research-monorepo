# Flex twin: a rigid-body twin says any PD bandwidth is stable, how much does a flexible joint really tolerate?

Pure Python, no dependencies. Real joint: motor and load inertia coupled by a spring and damper; twin: one rigid inertia. With PD feedback of the load position, the twin is stable at every bandwidth, but the real loop is stable iff `ω_n < ω_n*`, the root of an exact cubic (matches the characteristic roots to 2e-16) that does not depend on the inertia ratio and is `≈ ζ_s/ζ` times the resonance: 7.1% at structural damping `ζ_s = 0.05`. Past it the real poles grow (+0.005 at 1.1 `ω_n*`, e-fold in 200 time units, +0.68 at 20×), and a bandwidth of 0.3 resonance needs `ζ_s ≥ 0.209`. Negative result: over a 50-time-unit step response the real-twin gap is 9.0e-3 at 1.1 `ω_n*` (already unstable) versus 2.1e-3 at 0.5 `ω_n*`, so a short validation passes a divergent design (it reaches 2e4 only by T=3000). Collocated (motor-side) feedback stayed stable at every gain tried. See `paper/whitepaper.md`.

```bash
cd research/flex-twin
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 8 tests, <2 s
PYTHONPATH=src python3 experiments/run.py                 # a few seconds; output in experiments/results.txt
```

**Builds on.** The digital-twin simulation-fidelity and sim-to-real direction of ARPG (<https://arpg.colorado.edu/>), HIRO Group (<https://hiro-group.ronc.one/>, manipulation) and the Autonomous Systems IRT (<https://www.colorado.edu/irt/autonomous-systems/>); no specific paper from those groups is reproduced and nothing here is affiliated with or endorsed by them. The method is classical: elastic-joint modelling (Spong 1987), non-collocated flexible-arm control (Cannon & Schmitz 1984) and Routh–Hurwitz analysis. Companion to `backlash-twin`, `control-twin` and `latency-twin` in this repository.

Stylised: linear single joint, continuous-time exact-derivative PD, simulated "real" system of the same structure as the model, no field data. MIT.
