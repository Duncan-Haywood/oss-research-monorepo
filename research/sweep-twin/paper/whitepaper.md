# An instantaneous-scan twin of a spinning lidar: how a moving robot skews walls, what speed that allows, and how accurate a deskew velocity must be

## Question
Lidar twins usually return the whole scan from one pose. A real spinning lidar sweeps its beams over a scan period `T` (0.1 s at 10 Hz) while the robot moves, so the scan is recorded against a pose that changes during the sweep. A perception stack tuned or a policy trained on the twin's clean scans meets a systematic distortion only at speed. How large is it, which motions cause it, how does it enter a heading estimate, what speed does it cap, and how accurate must a deskew velocity be?

## Model
Real sensor: a 2-D lidar with constant sweep rate `ω = 2π/T`, 1800 beams per scan, beam `k` fired at `t = 2πk/(nω)`. The robot translates with constant velocity `v` (and in one experiment rotates at constant yaw rate `Ω`). Each beam is ray-cast exactly against the room's walls from the robot's pose at that beam's time; the returned point is recorded in the sensor frame as if the scan were instantaneous. Twin: the same sweep from a single pose (`v = 0`, `Ω = 0`). A wall `n·x = d` with unit normal `n` is hit by the beam at angle `δ` from the normal at time `t = t₀ + δ/ω`. In the sensor frame the hit is `(s, h) = ((d − vₙt) tan δ, d − vₙt)` with `vₙ = n·v`. The normal coordinate is exactly linear in `t`, so the wall stays straight but its normal turns by `ψ ≈ vₙ/(ωd) = vₙT/(2πd)` and it shifts by `vₙ t₀`. Only the velocity component normal to the wall matters. Walls are fitted by total least squares over a sector of azimuth; "skew" is the error of the fitted normal angle. Pure Python, no dependencies.

## Results
(all numbers from `experiments/results.txt`)
1. **Skew is first-order `vₙT/(2πd)`.** A wall 5 m ahead at `T = 0.1 s`: fitted skew 0.173°, 0.349°, 0.894°, 1.860°, 4.041° at `v = 1, 2, 5, 10, 20 m/s`, against 0.182°, 0.365°, 0.912°, 1.824°, 3.648° from the formula with the start distance (errors 2% to 10%) and 0.184° … 4.304° with the distance at the hit (within 7%). The twin gives 0 at every speed. The fitted distance is also biased short by `vₙt₀` (4.62 m at 10 m/s).
2. **Only the normal component counts.** At 10 m/s: 1.860° for a wall ahead, exactly 0 for motion parallel to it, 1.285° for oblique motion (7.07, 7.07).
3. **Scaling.** Skew is linear in `T` and in `1/d`: at 10 m/s, `T = 0.05/0.1/0.2 s` gives 0.894°/1.860°/4.041° at 5 m, and at 2 m and `T = 0.2 s` the skew is 13.5°.
4. **Heading from a room.** Averaging the fitted-minus-nominal normal angle over four walls (±5° sectors, 5 m/s along x): front and back walls skew in opposite senses, so a centred 10 × 10 m room cancels to 0.027° (front +0.946°, back −0.837°), but a room with the robot 2 m from the back wall and 18 m from the front gives −0.403° (front +0.256°, back −1.867°) and a 42 m hall −0.438°: the nearest wall dominates. The twin gives 0 in all three.
5. **Speed limits.** `v* = 2π d ψ_tol/T`: for a 1° tolerance, 5.48 m/s at `d = 5 m, T = 0.1 s`, 2.19 m/s at 2 m, and 10.97 m/s at 10 m or at `T = 0.05 s`. Check: at 5.48 m/s the fitted skew is 0.984° (the formula is first order; the fitted distance has already shrunk to 4.79 m).
6. **Deskewing with the wrong velocity.** Re-expressing points with `v_est` removes the skew exactly when `v_est = v` (0.000°), and otherwise leaves `(vₙ − v_est)T/(2πd)`: residual 0.092°, 0.185°, 0.370°, 0.926° for 5%, 10%, 20%, 50% velocity error at 10 m/s (formula 0.099°, 0.197°, 0.395°, 0.986°, 7% high). A 0.5° residual tolerance needs the normal velocity known to 27% at `d = 5 m`, 1° to 55%; at shorter range and faster scans the tolerance is proportionally tighter.
7. **Yaw rate bends rather than rotates.** With no translation, a yaw rate of 0.5/1/2/4 rad/s leaves a fitted wall tilted by the heading at the moment of the hit (`Ωt_hit`: −1.074° … −8.594°; tilt minus heading is −0.009° … −0.590°) and a curvature: maximum departure from the best line 3.3, 6.7, 13.5, 27.6 mm, linear in `Ω`. I did not derive the curvature constant.

## Limitations
2-D, one planar wall per fit, constant velocity and yaw rate over a scan, exact ray-casting with no range noise, beam divergence, mixed pixels, intensity or dropout (see `beam-twin`, `dropout-twin`); the skew formula is first order and is 10% off by 4° of skew. The heading estimate is a weighted mean of per-wall angles, not scan matching against a map, so the magnitudes in item 4 are not those of a real registration. Deskewing assumes the velocity is constant and known up to a scalar error; a real estimator would also err in direction and time. A simulated "real" sensor, no measured lidar; nothing here transfers to hardware.

## Next steps
Scan-to-map registration with and without deskew to get the real heading and drift cost; constant-velocity-error deskew inside a factor-graph odometry; 3-D spinning sensors (per-ring timing, `ψ` per ring); a rolling-shutter radar with the same timing structure; jointly estimating `v` from the skew itself (skew of front and back walls gives `v` directly: `vₙ = ψ ω d`); linking to `shutter-twin` and `lens-twin` for the camera analogues.

## References
- Zhang, J. & Singh, S. (2014). LOAM: Lidar odometry and mapping in real-time. *RSS*.
- Bosse, M. & Zlot, R. (2009). Continuous 3D scan-matching with a spinning 2D laser. *ICRA*, 4312–4319.
- Zhao, W., Queralta, J. P. & Westerlund, T. (2020). Sim-to-real transfer in deep reinforcement learning for robotics: a survey. *IEEE SSCI*.
