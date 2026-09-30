# A two-sensor twin with synchronised clocks overstates gate recall and fusion gain at speed: one factor κ = 1 + v²s²/(2σ²) sets both

*Stylised: two position sensors with Gaussian noise, one target moving at constant speed, Gaussian timestamp jitter. Pure Python; every number is from `experiments/results.txt` (seeded, seconds). No robot or radar data. Negative and non-monotone results are reported as such.*

## Question
Radar–lidar or multi-robot simulators usually stamp every sensor with one perfect clock. Real pairs of sensors are off by a jittery offset `δ`, which turns into a position error `vδ` for a target moving at speed `v`. A gate tuned for 99% association recall in the twin, and a fusion rule that averages the two sensors, are both tuned without that error. How wrong are they, at which speeds, and what does repairing the gate cost?

## Model
Sensors A (reference clock) and B report a target's position with independent `N(0,σ²)` errors, `σ=0.2` m. B's timestamp is off by `δ~N(0,s²)` per scan pair (jitter), so `z_B − z_A ~ N(0, 2σ²+v²s²)`; the twin has `s=0`. Detections are associated if `|z_B−z_A|<g`; the twin's gate for recall `r` is `g=z_{(1+r)/2}√2σ` (0.7286 m for r=0.99). Define `κ = 1+v²s²/(2σ²)`. Then (i) exact recall is `2Φ(g/(σ√(2κ)))−1`; the recall-restoring gate is `√κ` times the twin's; (ii) the equal-weight fused MSE at the reference time is `κσ²/2` (the twin says `σ²/2`), it beats sensor A alone iff `κ<2`, the optimal B weight is `σ²/(2σ²+v²s²)` with MSE `σ²(σ²+v²s²)/(2σ²+v²s²)<σ²`; (iii) for a constant offset `d0`, recall is `Φ((g−vd0)/(√2σ))−Φ((−g−vd0)/(√2σ))`; (iv) a second target moving alike at separation `D` falls in the gate with probability `Φ((g−D)/(σ√(2κ)))−Φ((−g−D)/(σ√(2κ)))`.

## Results
1. **Formulas match simulation** (200 000 pairs): recall 0.9888/0.9886 (v=5 m/s, s=10 ms), 0.9645/0.9645 (10, 20 ms), 0.8630/0.8623 (20, 20 ms), 0.5167/0.5170 (20, 50 ms). Equal-weight fused MSE/σ²: 0.5156/0.5153, 0.7500/0.7502, 1.5000/1.4969, 6.750/6.738.
2. **The twin's 99% is speed-blind.** Real recall of its gate at s=10 ms: 0.990 / 0.989 / 0.985 / 0.965 / 0.923 at v = 2 / 5 / 10 / 20 / 30 m/s; at s=20 ms: 0.989 / 0.985 / 0.965 / 0.863 / 0.728; at s=50 ms: 0.985 / 0.946 / 0.795 / 0.517 / 0.367. Recall falls to 0.95 at v = 48.2 / 24.1 / 12.1 / 4.8 m/s for s = 5 / 10 / 20 / 50 ms (to 0.90 at 68.2 / 34.1 / 17.0 / 6.8), i.e. `v*∝1/s`.
3. **Jitter versus constant offset of the same rms shift** `vs` (recall of the twin's gate): 0.9848 vs 0.9852 (0.1 m), 0.9645 vs 0.9687 (0.2 m), 0.8630 vs 0.8773 (0.4 m), but 0.7279 vs 0.6753 (0.6 m). The constant offset is slightly kinder for small shifts and worse for large ones; neither ordering is general.
4. **Fusion gain reverses.** Equal weights give MSE 0.516 / 0.750 / 1.500 / 6.750 σ² at (v,s) = (5,10 ms) / (10,20) / (20,20) / (20,50) against the twin's 0.5; they are worse than sensor A alone once `vs > √2σ = 0.283` m. The optimal weight on B falls 0.485 / 0.333 / 0.167 / 0.037 and gives 0.515 / 0.667 / 0.833 / 0.963 σ² (simulated 0.515 / 0.667 / 0.834 / 0.962).
5. **Repairing the gate costs neighbour confusion.** At (v,s)=(20 m/s, 20 ms) the gate must grow from 0.729 to 1.262 m (×√3); a neighbour 1.0 m away is then inside it with probability 0.704 (0.290 with the twin's gate, 0.169 in the twin's own world). At (10, 20 ms) the gate grows to 0.892 m and confusion at D=1.0 m goes from 0.217 to 0.378. At D=0.7 m, less than the gate, the twin-gate confusion is not monotone in jitter (0.5402 at s=0, 0.5328 at 10 m/s and 20 ms, 0.4263 at 20 m/s and 50 ms) because the wider difference distribution puts less mass near the neighbour; with the repaired gate it rises to 0.71–0.97.

## Limitations
One target, one axis, constant speed, independent Gaussian errors, jitter independent of position and known to the designer; association by a fixed gate rather than nearest-neighbour or joint assignment; the neighbour moves identically, and only pairwise confusion is computed. No tracking filter, no clutter or missed detections, no rolling-shutter or scanning-time skew, no time-varying clock drift. Offset is a position error `vδ` only (no orientation). Nothing is estimated from real sensor data, and the contribution is the exact form of the κ factor, not a new estimator.

## Next steps
Timestamp offset estimation from the data itself (the offset is identifiable from moving targets, cf. Olson 2010; Furgale et al. 2013) and how much it recovers; nearest-neighbour and global-nearest-neighbour association with clutter; a Kalman filter whose measurement covariance ignores `v²s²`; multi-robot map merging where each robot's clock drifts; the same factor for radar Doppler-range coupling in the radar twins of this repository.

## References
- Bar-Shalom, Y. & Fortmann, T. E. (1988). *Tracking and Data Association*. Academic Press.
- Bar-Shalom, Y., Li, X. R. & Kirubarajan, T. (2001). *Estimation with Applications to Tracking and Navigation*. Wiley.
- Olson, E. (2010). A passive solution to the sensor synchronization problem. *IROS*, 1059–1064.
- Furgale, P., Rehder, J. & Siegwart, R. (2013). Unified temporal and spatial calibration for multi-sensor systems. *IROS*, 1280–1286.
