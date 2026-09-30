# Closing the loop in simulation: a twin with independent odometry noise certifies chains that are too long

*Stylised: 1-D pose chain, one loop closure, linear residual spreading, Gaussian noise. Base case `n=40`, `σ=σ_c=1 cm`; real bias random walk with per-step variance `q`; a chosen model, not data. Pure Python; every number is from `experiments/results.txt`.*

## Question
A mapper's loop-closure gain and the "how long may I run before I must close a loop" rule are tuned in a simulator whose odometry noise is independent per step. Real odometry (wheel slip, IMU bias, terrain) has drifting bias. What does the twin get wrong, the gain or the claim, and how many ground-truthed runs does it take to notice?

## Method
Odometry errors `ε_i`; residual `ρ = v − S_n`; pose `k` is corrected by `h_k ρ`. For any covariance of `ε`, `Var(x̂_k − x_k) = v_k − 2h_k a_k + h_k²W`, exact, minimised by `h_k = a_k/W`. The twin uses `h_k = g_t k` and claims `kσ² − k²σ⁴/(nσ²+σ_c²)`. Reality: `ε_i = b_i + e_i`, `b_i = b_{i−1}+w_i`, `Var w = q`. Covariances are summed exactly.

## Results
1. **Verification.** At `q=1e-6` the exact error variance at `k=10,20,30,40` (1.47e-3, 2.27e-3, 1.47e-3, 1.11e-4) matches 60k-run Monte Carlo within 1.5%; the twin claims 7.6e-4, 1.02e-3, 8.0e-4, 9.8e-5.
2. **Constant drift is benign, contrary to intuition.** A shared constant bias `b~N(0,β²)` in every increment is almost exactly what the linear spread removes: worst-pose sd is 0.03202 / 0.03207 / 0.03370 at `β` = 0.002 / 0.004 / 0.02 against the twin's 0.03201. Only drift that *changes* along the chain is a problem here.
3. **Drifting bias makes the claim overconfident.** Worst-pose sd, real vs claimed 0.03201: 0.0339 (`q=1e-7`, ×1.06), 0.0476 (×1.49, `1e-6`), 0.0774 (×2.42, `4e-6`), 0.1159 (×3.62, `1e-5`). The twin's gain hardly moves (`g n` = 0.976 vs the pose-`n`-optimal 0.984–1.000), and using the end-matching gain is not better for the worst pose (0.0484 vs 0.0476, 0.0797 vs 0.0774): a gain fitted from the loop-residual variance, the obvious calibration, does not repair the map. Even the best per-pose shares `a_k/W`, which need the real covariance, reduce the worst-pose sd only to 0.0336 / 0.0419 / 0.0609 / 0.0874 — the residual carries too little information to undo interior drift.
4. **A twin-certified loop-closure interval is too long.** Rule: largest `n` whose worst-pose sd ≤ 4 cm. The twin certifies 62 steps regardless of `q`; the real limit is 51 (`q=1e-7`), 33 (`1e-6`), 23 (`4e-6`), with the twin's gain or the end-matching gain alike. At 62 steps the real worst-pose sd is 4.5 / 7.9 / 14.3 cm.
5. **Auditing the claim.** Test: mean of `m` squared errors at pose 20 over the claim, one-sided at 5% (size checked: 0.050 at `m=10` and 100). True ratio 1.12 (`q=1e-7`): power 0.06 / 0.07 / 0.09 / 0.13 / 0.22 at `m` = 1 / 3 / 10 / 30 / 100. Ratio 2.21 (`1e-6`): 0.19 / 0.32 / 0.60 / 0.92 / 1.00. Ratio 5.84 (`4e-6`): 0.41 / 0.72 / 0.98 / 1 / 1. Mild misclaims are hard to detect; at a ratio of ~2, tens of ground-truthed chains are needed.

## Limitations
1-D, one closure, a fixed linear share rule; a real pose graph optimiser with many closures, rotations and robust kernels would distribute the residual differently, and the negative result in item 3 is specific to the linear-share family and to this drift model. The drift is one stylised family; parameters are chosen, not fitted. Audit powers assume Gaussian errors at one pose and a known claim. Not tested on real or simulated (Gazebo/Isaac) odometry.

## Next steps
Full pose-graph optimisation with several closures and the value of an extra closure under the twin's versus the real claim; fit `q` from repeated loops with a state-augmented (bias) estimator and quantify the benefit; multi-robot map merging where inter-robot closures inherit each twin's claim; validation against logged odometry from a real vehicle.

## References
- Thrun, S., Burgard, W. & Fox, D. (2005). *Probabilistic Robotics*. MIT Press.
- Cadena, C. et al. (2016). Past, present, and future of simultaneous localization and mapping. *IEEE T-RO*. arXiv:1606.05830.
- Bar-Shalom, Y., Li, X. R. & Kirubarajan, T. (2001). *Estimation with Applications to Tracking and Navigation*. Wiley.
