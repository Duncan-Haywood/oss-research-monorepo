# Windup twin: a twin without actuator saturation says the PI loop undershoots 14%, what does the real loop do after a large step?

Pure Python, no dependencies. Integrator plant `ẋ = u` under PI control `u = −sat_U(kp x + ki z)`, `ż = x`, step `x0`, twin = no saturation. The twin's undershoot past the target is a fixed fraction of `x0` (`e⁻² = 13.5%` at ζ = 1, 21.0% at ζ = 0.7). The real loop is identical while `a = kp x0/U ≤ 1`; beyond that the integrator winds up during the saturated approach and the real undershoot is exact in closed form (saturated parabola, quadratic exit time, then the linear loop): ζ = 1 gives 18.7% (a = 2), 43.9% (5), 81.5% (20), 96.1% (100) against the twin's 13.5%, matching RK4 simulation to 4–5 digits. Deep in saturation `1 − undershoot → kp U/(ki x0) = 4ζ²/a`, so the loop returns almost the whole step to the wrong side and the real/twin ratio tends to `1/twin` (7.4× at ζ = 1, 20.9× at ζ = 2). Since the twin certifies every bandwidth, the real design rule is a cap on depth: undershoot ≤ 25% needs `a ≤ 1.5 / 2.7 / 9.2` for ζ = 0.7 / 1 / 2. Conditional integration replays the twin from `x = U/kp`, so its absolute undershoot is `twin·U/kp`, independent of `x0` (simulated to 3 digits for ζ ≥ 0.7; at ζ = 0.3 the replay itself saturates and the formula is an upper bound). Stylised: first-order plant, symmetric saturation, noiseless; see `paper/whitepaper.md`.

```bash
cd research/windup-twin
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 9 tests, about 3 s
PYTHONPATH=src python3 experiments/run.py                 # about 15 s; output in experiments/results.txt
```

**Builds on.** The digital-twin simulation-fidelity and sim-to-real direction of ARPG (<https://arpg.colorado.edu/>), HIRO Group (<https://hiro-group.ronc.one/>, manipulation) and the Autonomous Systems IRT (<https://www.colorado.edu/irt/autonomous-systems/>) and RECUV (<https://www.colorado.edu/recuv/>, UAV and field-robot simulation); no specific paper from those groups is reproduced and nothing here is affiliated with or endorsed by them. Integrator windup and conditional integration are classical (Åström & Hägglund 2006). Companion to `saturation-twin` and `slew-twin` in this repository, which cover amplitude saturation of unstable plants and rate limits.

Stylised: integrator plant, PI loop, one symmetric amplitude limit, noiseless, a simulated "real" system, no field data. MIT.
