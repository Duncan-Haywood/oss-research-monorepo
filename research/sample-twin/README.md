# Sample twin: a continuous-time twin promises any bandwidth, what does a real controller sampled every T allow?

Pure Python, no dependencies. Unit mass under PD control `u = −kp x_k − kd v_k` sampled every `T` and held (zero-order hold); the twin runs the same law in continuous time, whose closed loop `s² + kd s + kp` is stable for every positive gain. The exact sampled loop has trace `2 − kpT²/2 − kdT` and determinant `1 − kdT + kpT²/2`, and is stable iff `kp T/2 < kd < 2/T`, i.e. `ε = ωnT < min(4ζ, 1/ζ)` (window equals the multiplier moduli in 48 of 48 grid cases; the discretisation matches an RK4 simulation of the continuous plant to 2·10⁻¹⁴). Consequences: a hard cap `ωnT < 2` (`fn < fs/π`) for every damping, attained only at ζ = ½ (random search: 0 stable of 65 203 draws above it); two different failure mechanisms, a *delay* branch for ζ < ½ (the hold acts as a lag `T/2`, matching the `lag-twin` limit exactly; the loop hunts at `2 asin(ε/2)/T`, 0.7–16% above the twin's own `ωn`) and a *derivative* branch for ζ > ½ (`kdT = 2`, multiplier −1, period-2 chatter the twin never shows); a deadbeat point (`ε = 1`, ζ = ¾) where the real loop settles in two samples while the twin promises `e^{−0.75}` per step; and a step-test RMS error ≈ 0.053 ε that gives no warning of a cliff at ε = 1.43 (ζ = 0.7). Stylised: linear, one mass, no noise or delay; see `paper/whitepaper.md`.

```bash
cd research/sample-twin
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 8 tests, well under a second
PYTHONPATH=src python3 experiments/run.py                 # about a second; output in experiments/results.txt
```

**Builds on.** The digital-twin simulation-fidelity and sim-to-real direction of ARPG (<https://arpg.colorado.edu/>), HIRO Group (<https://hiro-group.ronc.one/>, manipulation) and the Autonomous Systems IRT (<https://www.colorado.edu/irt/autonomous-systems/>) and RECUV (<https://www.colorado.edu/recuv/>, UAV and field-robot simulation); no specific paper from those groups is reproduced and nothing here is affiliated with or endorsed by them. The sampled-data stability conditions and deadbeat control are classical (Åström & Wittenmark 1997; Franklin, Powell & Workman 1998). Companion to `lag-twin` (continuous actuator lag, the ζ < ½ branch here), `latency-twin` (whole-sample sensor delay), `timestep-twin` (the twin's own integrator step, not the real controller's rate), `slew-twin` and `control-twin` in this repository.

Stylised: unit mass, PD loop, exact ZOH, noiseless, a simulated "real" system, no field data. MIT.
