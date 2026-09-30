# A saturation-free twin understates PI undershoot by up to `1/twin`: integrator windup, exactly

*Stylised: an integrator plant under PI control, pure Python, every number is from `experiments/results.txt` (deterministic, about 15 s). The "real" system is itself simulated; no lab or field data. Negative and out-of-model results are marked.*

## Question
A controller tuned in a twin whose actuator never saturates is then given a large step on hardware whose actuator does. How much worse is the undershoot past the target than the twin reported, how does it depend on step size and bandwidth, and what does the standard fix buy?

## Model
Real: `ẋ = −sat_U(v)`, `v = kp x + ki z`, `ż = x`, `x(0) = x0 > 0`, `z(0) = 0`, `kp = 2ζωn`, `ki = ωn²`. Twin: no saturation, so `z̈ + kp ż + ki z = 0` with `x = ż`, `x'(0) = −kp x0`. By linearity the twin's undershoot `−min x/x0` is independent of `x0` (`e⁻²` at ζ = 1, 0.2103 at ζ = 0.7, 0.0478 at ζ = 2; simulation agrees to 5 digits). Define the saturation depth `a = kp x0/U`; everything depends only on `(ζ, a)` (time scaling).

## Results
1. **Exact real undershoot.** For `a ≤ 1` the command never saturates and real = twin. For `a > 1`: during saturation `x = x0 − Ut`, `z = x0 t − Ut²/2`; `v` returns to `U` at the larger root `t1` of `(kiU/2)t² − (ki x0 − kp U)t − (kp x0 − U) = 0`; from `(x1, x' = −U)` the linear loop gives the first extremum in closed form (critical, over- and underdamped cases). This matches RK4 simulation to 5 digits in all 18 (ζ, a) cases in `results.txt` section 1. At ζ = 1: undershoot 18.7% (a = 2), 43.9% (5), 81.5% (20), 96.1% (100) vs the twin's 13.5%, i.e. 1.4×, 3.2×, 6.0×, 7.1×. At ζ = 2 the ratio reaches 17.8× at a = 100.
2. **Deep saturation returns the whole step.** The saturated motion is time-symmetric (`x` goes from `x0` to `−x0`), and numerically `(1 − undershoot)·a/(4ζ²) → 1` (1.0000 at a = 10⁵ for ζ = 0.3, 0.7, 1, 2), i.e. `1 − undershoot ≈ kp U/(ki x0)`. This limit is read off numerically and supported by the test at `a = 10⁶`, not proved here. The real/twin ratio therefore tends to `1/twin`: 2.2× (ζ = 0.3), 4.8× (0.7), 7.4× (1), 20.9× (2). More damping makes the twin look better and the gap larger.
3. **The twin cannot bound bandwidth; depth can.** At fixed `x0` and `U`, raising `ωn` raises `a = 2ζωn x0/U`. For ζ = 1, `x0 = U = 1` the twin says 13.5% at every `ωn`; the real loop gives 13.5% (ωn ≤ 0.5), 18.7% (1), 36.4% (2), 66.1% (5), 81.5% (10), 96.1% (50). The largest depth meeting an undershoot target of 25%, 30%, 40%, 50% is `a* =` 1.50, 1.83, 2.46, 3.21 (ζ = 0.7), 2.72, 3.27, 4.46, 5.97 (ζ = 1), 9.24, 11.3, 16.0, 22.0 (ζ = 2) (bisection on the exact formula), i.e. `ωn ≤ a* U/(2ζ x0)`.
4. **Conditional integration.** Freezing `z` while `|v| > U` and `v x > 0` re-enters the linear regime from `x = U/kp`, `z = 0`, exactly the twin's trajectory from `x0' = U/kp`, so the absolute undershoot is `twin·U/kp` independent of `x0` (as a fraction of `x0`: 0.0677, 0.00677, 0.00135 at ζ = 1, a = 2, 20, 100 vs windup 18.7%, 81.5%, 96.1%). Simulation agrees to ≤ 3·10⁻⁵ for ζ = 0.7, 1, 2. **Negative:** at ζ = 0.3 the replayed trajectory itself saturates on the far side and the simulation is 0.74 of the formula (0.166 vs 0.225 at a = 2), so there the formula is only an upper bound.

## Limitations
First-order plant (the undershoot fractions are specific to it), symmetric amplitude limit, step from rest with `z(0) = 0`, PI only, continuous time, noiseless; no rate limit (`slew-twin`), no unstable plant (`saturation-twin`), no sampling. Conditional integration is the simplest anti-windup; back-calculation is not analysed. The closed form assumes the loop stays unsaturated after the first exit; this held in every simulated case with ζ ≥ 0.3 here but is not proved in general. Not evidence about any particular actuator.

## Next steps
A proof of the deep-saturation limit and of the no-resaturation condition; back-calculation gain versus the clamp; second-order plants where windup interacts with the lag limit of `lag-twin`; estimating `U` from a few large logged commands and testing the twin's saturation-free claim with the sequential test in `twin-audit`.

## References
- Åström, K. J. & Hägglund, T. (2006). *Advanced PID Control*. ISA.
- Åström, K. J. & Murray, R. M. (2008). *Feedback Systems: An Introduction for Scientists and Engineers*. Princeton University Press.
- Zhao, W., Queralta, J. P. & Westerlund, T. (2020). Sim-to-real transfer in deep reinforcement learning for robotics: a survey. *IEEE SSCI*.
