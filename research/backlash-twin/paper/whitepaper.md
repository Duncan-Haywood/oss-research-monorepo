# Gear play a twin does not model: exact limit cycles, rest states and bistability of a tracking loop

*Stylised: scalar integral servo, symmetric backlash of half-width `d = 0.1`, K=0.5, square-wave reference. Pure Python; every number is from `experiments/results.txt` (deterministic, <1 s). The "real" system is itself simulated; no lab or field data.*

## Question
A controller is validated in a twin whose actuator is rigid. On the real robot the gears have play. How wrong is the twin's tracking-error estimate for a reversing reference, and can the twin predict the real behaviour at all?

## Model
Motor `m⁺ = m + K(r − x)`; gap `g = m − x ∈ [−d, d]`. If `|g + K(r−x)| ≤ d` the load stays put; otherwise the load moves by the excess and the gap sticks at `±d`. Twin: `x = m`. Reference: `r = +A/2` for `P` steps, `−A/2` for `P` steps, repeating. Twin quantities are exact: swing `(A/2)(1−ρ)/(1+ρ)`, `ρ=(1−K)^P`, and rms error from the geometric decay of `e = A/2 + a`.

## Results
1. **Moving cycle, exact.** Assume a symmetric cycle with swing `a`. After a reversal the load is stuck with constant error `e0 = A/2 + a` for `n = ⌈2d/(K e0)⌉` steps, jumps by `nKe0 − 2d`, then decays by `(1−K)` per step. Periodicity gives `a(1+q) = (A/2)(1−q) − 2dc`, `c=(1−K)^{P−n}`, `q=c(1−nK)`; a candidate `n` is consistent iff `(n−1)Ke0 ≤ 2d < nKe0`. In simulation the swing and rms error equal the formula to every printed digit for A ∈ {0.085, 0.1, 0.2, 0.5, 1} (unique cycle). Real/twin rms error: 1.98× at A=0.1, 1.58× at 0.2, 1.25× at 0.5, 1.11× at 1.0.
2. **Rest.** The load can stay at `x=0` iff the motor excursion fits in the play, `KPA/2 ≤ 2d`. Then the rms error is exactly `A/2`: at A=0.05 it is 0.0250 vs the twin's 0.0182 (1.37×). For A ≤ 0.06 no symmetric moving cycle exists; some initial gaps (g0 = +d/2 at A=0.05, swing 0.0110, error 0.0258; g0 = +d/2, +d at A=0.03, swing 0.0146) gave irregular partial motion instead, with a larger error than rest; this is observed, not explained here.
3. **Bistability.** At A = 0.065, 0.07, 0.075 two symmetric cycles exist for the moving branch and the rest state also exists; simulation from g0 = −d rests (swing 0.0000, error 0.0325 / 0.0350 / 0.0375) while every other tested g0 lands on the larger moving cycle (swing 0.0257 / 0.0305 / 0.0339, error 0.0525 / 0.0563 / 0.0591). The loop's behaviour depends on its history, not just its parameters; the twin has one answer.
4. **Scaling with `P`.** At the rest threshold `A_s = 4d/(KP)` the real/twin error ratio is 1.0, 1.4, 1.9, 2.7 for P = 5, 10, 20, 40.

## Limitations
One gain, one `d`, symmetric play, no measurement noise (deadband work in this repository shows noise can change the sign of such errors), square-wave reference only. Rest and bistability are demonstrated on a grid of initial gaps, stability of each cycle is not proved, and asymmetric outcomes are not characterised. Real gears have compliance and friction. Not a claim about any specific robot.

## Next steps
Noise and backlash together; characterise the asymmetric rest set; sinusoidal references and describing-function comparison; joint estimation of `d` from logs; compensation (backlash inverse) residuals.

## References
- Nordin, M. & Gutman, P.-O. (2002). Controlling mechanical systems with backlash — a survey. *Automatica* 38(10), 1633–1649.
- Tao, G. & Kokotović, P. V. (1996). *Adaptive Control of Systems with Actuator and Sensor Nonlinearities*. Wiley.
