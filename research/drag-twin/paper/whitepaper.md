# A linear-drag twin fitted by coast-down matches one speed and gets the dynamics, the stopping distance and the energy wrong elsewhere

## Question
Vehicle and drone twins often model drag as linear, `c v`, and fit `c` from a coast-down test. Real aerodynamic drag at these speeds is close to quadratic, `k v²`. What does such a twin get right (the steady state at the calibration speed) and what does it get wrong (time constants, coasting distance, energy at other speeds), and does a different calibration rule repair it?

## Model
Unit-mass vehicle, real `v' = F − k v²` with `k = 0.5`, `v ≥ 0`; twin `v' = F − c v`. Everything real is closed form: coast-down `v(t) = v0/(1+k v0 t)` (time to reach `v_f`: `(1/v_f − 1/v0)/k`, distance `ln(v0/v_f)/k`, with no stopping point), terminal speed `√(F/k)`, and the force-step response in tanh form (tests check these against RK4 to 1e-8). Twin closed forms: `v0 e^{−ct}`, distance `(v0−v_f)/c`, terminal speed `F/c`. Calibration rules: *secant* `c = k v_cal` (matches the drag force at `v_cal`), *tangent* `c = 2k v_cal` (matches the slope), and data fits (log-speed regression; through-origin regression of deceleration on speed). Pure Python.

## Results
(all numbers from `experiments/results.txt`)
1. **Coasting.** Secant-calibrated at `v0 = 10` (`c = 5`): the twin stops within distance `v0/c = 2.0`; the real vehicle needs 4.6 to fall to 0.1·`v0`, 9.2 for 0.01·`v0`, and its distance is logarithmically unbounded (27.6 at 10⁻⁶·`v0`). Time to reach 0.01·`v0`: real 19.8, twin 0.92. The two agree in nothing except the very start.
2. **Energy and steady state.** The secant twin has the exact steady state at `v_cal` and is wrong everywhere else by exactly the speed ratio: energy per distance twin/real `= v_cal/v` (0.30 at `v = 10` for `v_cal = 3`; 5.0 at `v = 2` for `v_cal = 10`). A mission planned in the twin at 1.5× the calibration speed under-predicts drag energy by 33%.
3. **Dynamics are off by a factor 2 even at the calibration speed.** Small force step about `v* = 6`: real time constant 0.1666, secant twin 0.3333, ratio 2.001 (exactly 2 by linearisation: real slope `2kv*`, twin `kv*`). Tangent calibration fixes the time constant (ratio 1.000) but then predicts half the real steady-state speed gain: terminal speed 0.5× real. No single `c` gets both, because a linear law cannot have the same value and slope as `k v²` at one point. For a 4× force step the real response is faster (0.0993) and the twin ratios are 3.36 (secant) and 1.68 (tangent).
4. **Closed loop.** A proportional speed hold `u = F0 + Kp(v_ref − v)` tuned in the secant twin predicts rise times 1.86×, 1.60×, 1.22× too long at `Kp` = 0.5, 2, 10 (real poles 6.5, 8, 16 vs twin 3.5, 5, 13): weak feedback inherits the full factor 2, strong feedback masks it.
5. **What the data fits return.** Coast-down data from `v0 = 10`, noise sd 0.05, 20 seeds. Log-speed regression gives `c` = 3.43, 2.39, 1.63, 0.74 for windows 0.2, 0.5, 1.0, 3.0 (final speeds 5.0, 2.9, 1.7, 0.6): the fitted "drag" drifts to 0.15× the secant at `v0` as the window includes slow speeds. Deceleration-on-speed regression gives 3.75, 3.20, 2.91, 2.65, closer to the secant at the mid speed of the window but also falling with the window length; noise-free, uniform speeds on `[0, V]` give exactly `3kV/4`. The fit therefore encodes the test design, not a physical constant; two labs with different coast-down protocols get different twins.
6. **A fit over a band.** Regression on speeds `[5, 10]` gives `c = 4.02` (secant at 8.04): energy per distance twin/real is 8.0 at `v = 1`, 1.6 at 5, 0.80 at 10, 0.54 at 15.

## Limitations
One-dimensional, unit mass, constant `k`, no rolling resistance, no Reynolds-number dependence, no noise in the closed-form "real" system except in the fit experiment (Gaussian, small), one `k`. The closed-loop experiment is a proportional controller only, with an integration step and horizon chosen by me; the pole values are exact and the rise times are numerical. "Real" is simulated, not a wind-tunnel or field coast-down.

## Next steps
Drag law `a v + k v²` with both terms identified from data; fit-window design that recovers `k` (regress on `v²` not `v`); cross-check against a real UAV or rover coast-down log; wind (see `uav-energy-twin`), thrust-limited flight (`saturation-twin`), and propagation of the `2×` dynamics error into a tuned PI loop.

## References
- Hoerner, S. F. (1965). *Fluid-Dynamic Drag*. Hoerner Fluid Dynamics.
- Ljung, L. (1999). *System Identification: Theory for the User*, 2nd ed. Prentice Hall.
- Khalil, H. K. (2002). *Nonlinear Systems*, 3rd ed. Prentice Hall (linearisation).
- Zhao, W., Queralta, J. P. & Westerlund, T. (2020). Sim-to-real transfer in deep reinforcement learning for robotics: a survey. *IEEE SSCI*.
