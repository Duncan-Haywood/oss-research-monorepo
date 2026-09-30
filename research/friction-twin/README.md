# Friction twin: a twin with no dry friction says the PI loop converges, what does the real one do?

Pure Python, no dependencies. Real load moves through dry friction (breakaway level `fs`, sliding level `fc ≤ fs`); twin has none (or only Coulomb friction). On the discrete PI loop `z+=z+x, u=−(kp x+ki z), x+=u−s·fc` the frictionless twin's spectral radius is 0.707–0.894 (twin error <1e-123), and a Coulomb-only twin (`fs=fc`, a pure deadband) also comes to rest, yet with a stiction drop `d = fs−fc > 0` the real loop stick-slips forever at amplitude 0.47–0.92 `fs` for `fc = fs/2` (0.4810 at `(kp,ki)=(0.5,0.1)`). At `(0.5,0.1)` the amplitude is 0.89–0.98 of `d` for `d` from 0.01 to 1, independent of the start, but the ratio depends on the gains (0.96 at `kp=0.5`, 1.46 at `kp=0.3`, 1.84 at `kp=0.2`). The dynamics are homogeneous (trajectories scale bit for bit under power-of-two rescaling of the friction levels). A twin that assumes the wrong drop mispredicts the amplitude almost proportionally (−23% at `d̂=0.4`, +51% at `d̂=0.75` for true `d=0.5`). Negative results: small starts hunt where large ones converge (bistable for `ki ≤ 0.05`), and the cycle is stick-slip with 3–6 slide steps, not a sinusoid, so no describing-function amplitude is claimed. See `paper/whitepaper.md`.

```bash
cd research/friction-twin
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 7 tests, <1 s
PYTHONPATH=src python3 experiments/run.py                 # ~1 s; output in experiments/results.txt
```

**Builds on.** The digital-twin simulation-fidelity and sim-to-real direction of ARPG (<https://arpg.colorado.edu/>), HIRO Group (<https://hiro-group.ronc.one/>, manipulation) and the Autonomous Systems IRT (<https://www.colorado.edu/irt/autonomous-systems/>); no specific paper from those groups is reproduced and nothing here is affiliated with or endorsed by them. The method is classical: stick-slip and friction compensation (Armstrong-Hélouvry, Dupont & Canudas de Wit 1994; Olsson et al. 1998) and hunting under integral control (Åström & Hägglund). Follow-up to `backlash-twin`, `deadband-twin` and `slew-twin`, and companion to `control-twin` and `saturation-twin` in this repository.

Stylised: scalar massless load, constant friction levels (no Stribeck velocity dependence, no dwell-time or presliding effects), noiseless, a simulated "real" system, no field data. MIT.
