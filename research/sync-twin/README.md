# Sync twin: a two-sensor twin with perfectly synchronised clocks overstates gate recall and fusion gain at speed, and one factor sets both

Pure Python, no dependencies. Two sensors report a moving target's position with independent `N(0, 0.2²)` m noise; the twin stamps them with one clock, reality has a jittered offset `δ ~ N(0, s²)`, adding position error `vδ`. With `κ = 1 + v²s²/(2σ²)`, the association gate a twin tunes for 99% recall (0.7286 m) has exact real recall `2Φ(g/(σ√(2κ)))−1` (matched to simulation: 0.8630 vs 0.8623 at 20 m/s and 20 ms; 0.5167 vs 0.5170 at 20 m/s and 50 ms). Recall is 0.965 at 20 m/s with 10 ms jitter and 0.795 at 10 m/s with 50 ms; it falls to 0.95 at 48.2 / 24.1 / 12.1 / 4.8 m/s for s = 5 / 10 / 20 / 50 ms. Restoring 99% needs a gate `√κ` times larger (0.729 → 1.262 m at 20 m/s, 20 ms), which raises the chance a neighbour 1 m away is associated from 0.290 to 0.704. Equal-weight fusion has MSE `κσ²/2` against the twin's `σ²/2` (0.75 at 10 m/s and 20 ms, 6.75 at 20 m/s and 50 ms) and is worse than sensor A alone once `vs > √2σ`; the optimal weight on the late sensor is `σ²/(2σ²+v²s²)`. A constant offset of the same rms shift is slightly better than jitter for small shifts (0.9687 vs 0.9645 at 0.2 m) and worse for large ones (0.6753 vs 0.7279 at 0.6 m). See `paper/whitepaper.md`.

```bash
cd research/sync-twin
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 9 tests, ~2 s
PYTHONPATH=src python3 experiments/run.py                 # seconds; output in experiments/results.txt
```

**Builds on.** The radar/lidar sensor-simulation and multi-robot mapping direction of ARPG (<https://arpg.colorado.edu/>), and the UAV and field-robot simulation direction of RECUV (<https://www.colorado.edu/recuv/>); no specific paper from those groups is reproduced and nothing here is affiliated with or endorsed by them. The method is classical gated data association and sensor fusion (Bar-Shalom & Fortmann 1988; Bar-Shalom, Li & Kirubarajan 2001) with the time-offset problem as in Olson (2010) and Furgale, Rehder & Siegwart (2013). Companion to `latency-twin`, `doppler-twin` and `radar-clutter-twin` in this repository.

Stylised: one target, one axis, constant speed, independent Gaussian noise, known jitter, fixed-gate association, pairwise neighbour confusion only, simulated "real" data, no tracker and no clutter. MIT.
