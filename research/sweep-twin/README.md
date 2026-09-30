# Sweep twin: an instantaneous-scan twin of a spinning lidar returns clean walls at any speed, so how skewed are they on a moving robot, what speed does that cap, and how accurate must a deskew velocity be?

Pure Python, no dependencies. Real sensor: 2-D lidar, 10 Hz, 1800 beams, exact ray-casting against a rectangular room while the robot moves; twin: the whole scan from one pose. Results (all from `experiments/results.txt`): (1) a wall's normal is turned by `ψ ≈ vₙT/(2πd)` with `vₙ` the velocity component normal to the wall: fitted 0.173°–4.041° at 1–20 m/s for a wall 5 m ahead (formula within 2–10%), twin 0°; motion parallel to the wall gives exactly 0; (2) the range is biased short by `vₙt₀`; (3) skew scales with `T/d`, e.g. 13.5° at 10 m/s, `d = 2 m`, `T = 0.2 s`; (4) front and back walls skew in opposite senses, so a four-wall heading estimate cancels in a centred room (0.027°) but not with the robot near one wall (−0.403°); (5) the speed limit for a 1° skew is `v* = 2πdψ_tol/T` = 5.48 m/s at 5 m (fitted 0.984° there); (6) deskewing with a velocity wrong by 10% leaves 0.185° (formula 0.197°), and 0.5° tolerance needs the normal velocity to 27% at 5 m; (7) a yaw rate bends the wall (3.3–27.6 mm at 0.5–4 rad/s) instead of rotating it, constant not derived. Stylised: 2-D, constant velocity over a scan, no sensor noise, simulated "real" sensor; see `paper/whitepaper.md`.

```bash
cd research/sweep-twin
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 14 tests, well under 1 s
PYTHONPATH=src python3 experiments/run.py                 # about 1 s; output in experiments/results.txt
```

**Builds on.** The digital-twin sensor-simulation and sim-to-real perception direction of ARPG (<https://arpg.colorado.edu/>; lidar/radar sensing on moving field robots) and the Autonomous Systems IRT (<https://www.colorado.edu/irt/autonomous-systems/>) and RECUV (<https://www.colorado.edu/recuv/>); no specific paper from those groups is reproduced and nothing here is affiliated with or endorsed by them. Motion distortion in spinning-lidar data and its correction follow Bosse & Zlot (2009) and Zhang & Singh (2014). Companion to `beam-twin`, `dropout-twin`, `shutter-twin` and `lens-twin` in this repository.

Stylised: simulated "real" sensor, no measured lidar. MIT.
