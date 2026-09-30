# The twin that is right where it was fitted: an actuator deadband, and an exact excitation-dependent gain

*Stylised: a scalar static actuator `y = g D(u) + w` with `g=1, δ=0.5, σw=0.1`; Gaussian excitation. Pure Python; every number is from `experiments/results.txt` (seeded). The "real" system is itself simulated; no lab or field data. Negative and null results are reported as such.*

## Question
Manipulators, valves and gimbals have deadband (stiction, gear play, dead-zone compensation). A digital twin built as a linear actuator and fitted to logs will look well fitted. What gain does least squares recover, on which operating conditions does that gain transfer, what does it cost a controller built on the twin, and what is the cheapest repair?

## Model
Deadband `D(u) = u − δ·sign(u)` for `|u| > δ`, else 0. With `u ~ N(0, s²)` and `d = δ/s`, `cov(u, D(u)) = E[u²; |u|>δ] − δE[|u|; |u|>δ] = s²[2Q(d)+2dφ(d)] − 2s²dφ(d) = s²·2Q(d)` (the φ terms cancel), so the OLS gain converges to `g·2Q(d) = g·P(|z| > d)`, the probability of leaving the deadband (a Bussgang-type result). `Var D(u) = s²[2Q(d)(1+d²) − 2dφ(d)]`. For a sinusoid of amplitude `A>δ` the describing-function gain is `1 − (2/π)(asin r + r√(1−r²))`, `r=δ/A`, and 0 for `A ≤ δ`. The unit tests check each of these against simulation or numerical integration. The residual `e = gD(u)+w−bu` is uncorrelated with `u` but not independent of it.

## Results
1. **Fitted gain law** (n=2·10⁵, s=1): simulated `b` = 0.9998 / 0.8019 / 0.6167 / 0.3167 / 0.1349 / 0.0456 against `2Q(δ)` = 1.0000 / 0.8026 / 0.6171 / 0.3173 / 0.1336 / 0.0455 at δ = 0 / 0.25 / 0.5 / 1 / 1.5 / 2. Residual–input correlation is ≤2e-13 throughout. Linear-fit R² is 0.990 / 0.962 / 0.887 / 0.624 / 0.324 / 0.096, against 0.990 / 0.985 / 0.977 / 0.938 / 0.823 / 0.536 for the model that knows `D`. At small δ the linear twin is respectable on its own data, and it degrades gracefully, so a builder has no threshold at which it is obviously wrong.
2. **The gain does not transfer across excitation** (twin fitted at s=1, b=0.616, δ=0.5). Real gain `2Q(δ/s)` = 0.0000 / 0.0455 / 0.3173 / 0.6171 / 0.8026 / 0.9005 at s = 0.1 / 0.25 / 0.5 / 1 / 2 / 4. Twin/real is 13.5 at s=0.25, 1.94 at s=0.5, 0.998 at s=1, 0.77 at s=2, 0.68 at s=4. Held-out R² of the twin is −0.375 / −1.898 / 0.043 / 0.887 / 0.921 / 0.894: it fails outright at fine-motion scales, where it is worse than predicting the mean, and is only mediocre at 2× the fitted scale (twin/real 0.77).
3. **Feedforward.** With `u = r/b`, `b=0.617`, targets `r<δb=0.309` give exactly zero real output (r = 0.1, 0.2, 0.3). Real/target is 0.621 at r=0.5, then 1.121 / 1.371 / 1.521 at r = 1 / 2 / 5, tending to `1/b = 1.62` as the deadband shrinks relative to the command. The error changes sign with the target size, so no single gain correction fixes it.
4. **Closed loop.** In `x ← x + D(k(r−x))` the twin predicts convergence for 0<k<2; the real loop halts as soon as `|k e| ≤ δ`. The maximum final error over `e0 ∈ (0,5]` is exactly `δ/k`: 2.000 / 1.000 / 0.500 / 0.333 / 0.263 at k = 0.25 / 0.5 / 1 / 1.5 / 1.9, so raising the gain shrinks the stall band only down to `δ/2` before the twin's stability limit. At k=1, where the twin is deadbeat, the final error is exactly `min(|e0|, δ)` (0.300, 0.500, 0.500 for e0 = 0.3, 0.5, 2.0).
5. **Repair: fit the deadband** (train s=1, 300 repeats). Grid-plus-refinement fit of `(g, δ)`: g = 1.003 / 1.001 / 1.000 and δ = 0.502 / 0.501 / 0.500 at n = 100 / 300 / 1000, sd 0.027→0.008 and 0.022→0.006. Predicting at s=0.25 (RMSE / sd(y)): 0.952 for the deadband twin against 1.67 for the linear twin, where the noise floor `σw/sd(y)` is 0.965: the deadband twin is at the floor. This repair needs the *form* of the nonlinearity; a wrongly specified form (asymmetric or hysteretic) is not tested here.

## Limitations
Static map and known symmetric form; excitation is Gaussian, so the law `2Q` is specific to it (other input laws are not tested); the closed loop is a first-order integrator with exact state; no sensor noise, hysteresis or dynamics; the repair's δ grid assumes `δ < 2s`.

## Next steps
Hysteretic (backlash) rather than dead-zone nonlinearity; dynamic plants where deadband produces limit cycles with integral action; excitation design that identifies `δ` directly; combining with `saturation-twin` for dead-zone-plus-saturation actuators; validation on real servo logs.

## References
- Bussgang, J. J. (1952). Cross-correlation functions of amplitude-distorted Gaussian signals. *MIT RLE Tech. Rep. 216*.
- Price, R. (1958). A useful theorem for nonlinear devices having Gaussian inputs. *IRE Trans. Information Theory* 4(2).
- Gelb, A. & Vander Velde, W. E. (1968). *Multiple-Input Describing Functions and Nonlinear System Design*. McGraw-Hill.
- Zhao, W., Queralta, J. P. & Westerlund, T. (2020). Sim-to-real transfer in deep reinforcement learning for robotics: a survey. *IEEE SSCI*.
