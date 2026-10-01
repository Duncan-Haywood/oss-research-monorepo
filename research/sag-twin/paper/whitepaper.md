# An energy-bucket battery twin overstates flight time: closed-form sag losses, a power-dependent efficiency, and the payload they cost

## Question
UAV simulators often treat the battery as an energy bucket drained by the commanded power. A real pack has internal resistance and a voltage cutoff, so it delivers less energy at high power. How wrong is the bucket twin about runtime and payload, can one calibrated efficiency repair it, and how does pack-to-pack resistance spread turn that into mission shortfall?

## Model
Charge drawn `x` (Ah); open-circuit voltage `v(x) = V0 − m x`; series resistance `R`; constant power `P`. Terminal voltage `v_t = v − IR` with `I v_t = P`, so `I = 2P/(v + √(v²−4RP))`. The flight ends at the cutoff `v_t = V_c`, i.e. `v = v_c = V_c + RP/V_c`, or when `x = C`. Because `dt = dx/I` and `dv = −m dx`,

`t_real = (1/(2Pm)) ∫_{v_end}^{V0} (v + √(v² − 4RP)) dv`,

with `∫√(v²−a²) dv = v√(v²−a²)/2 − (a²/2) ln(v+√(v²−a²))`. The twin has `R = 0`: `t_twin = (V0² − v_end²)/(2mP) = E/P`. The delivered fraction is `η = t_real/t_twin`. Since `v_c ≥ 2√(RP)` (AM–GM) the cutoff always protects the square-root from going complex; a flight exists iff `v_c < V0`, i.e. `P < P_start = V_c (V0 − V_c)/R`. Hover power is `P(m) = P0 (m/m0)^{3/2}`.

## Results
(all from `experiments/results.txt`; pack: 6S, 25.2 → 18.0 V over 5 Ah, 108 Wh, cutoff 19.8 V)
1. **Closed form.** Matches midpoint integration of `dt = dx/I` to four decimals (e.g. 30.6651 min at R = 0.06 Ω, 150 W, twin 33.75), and the tests check an energy balance `P t = ∫(v − IR) dx`.
2. **Delivered fraction.** At 150 W: 0.954, 0.909, 0.818, 0.641 for R = 0.03, 0.06, 0.12, 0.24 Ω. At R = 0.12: 0.939 (50 W), 0.700 (250 W), 0.469 (450 W), 0.358 (550 W). Monotone decreasing in both `P` and `R` (tested).
3. **One-point calibration.** Fitting a constant efficiency (0.818) at 150 W, R = 0.12 gives errors −12.9%, −6.8%, 0, +17.0%, +40.3%, +74.4% at 50, 100, 150, 250, 350, 450 W. The uncalibrated twin overstates runtime by 22%, 72%, 113% at 150, 350, 450 W.
4. **Start limit.** `P_start` = 3564, 1782, 891, 446 W for R = 0.03…0.24 Ω; at R = 0.24 the real pack cannot fly 450 W at all while the twin claims 11.25 min.
5. **Payload for a 20-minute hover** (150 W at 1 kg): twin 0.417 kg (253 W); real 0.349, 0.288, 0.187, 0.034 kg for R = 0.03…0.24 Ω, so the twin overstates payload by 19.7%, 44.7%, 123.7%, 1123.5%. At the twin's payload the real runtime is 18.5, 16.9, 13.9, 8.1 min.
6. **Fleet shortfall** (R lognormal, median 0.12 Ω, σ = 0.35, an assumed spread). The twin's payload sits on its own boundary, so every pack falls short by construction; the shortfall is the informative quantity: median 13.9 min (30% short), 5th percentile 9.4 min, 1st percentile 6.7 min (Monte Carlo agrees to 0.03 min). Sizing at the (1−ε) quantile of `R` gives payload 0.187, 0.094, 0.063, 0.003 kg for ε = 0.5, 0.1, 0.05, 0.01 (cuts of 55%, 78%, 85%, 99% vs the twin); at 1% the pack can barely lift anything above the airframe.

## Limitations
Stylised, no battery data. Linear open-circuit curve and constant `R` (real `R` depends on state of charge, temperature, current and age); no RC transient; no Peukert or rate-capacity effect; no `I²R` heating feedback; a constant-power load and hover power from momentum theory only; the resistance spread is assumed. The twin is a naive baseline; a twin that fits `R` would match by construction, so the contribution is the size and shape of the error and the fact that one fitted efficiency is not enough, not a claim about any real pack.

## Next steps
Fit `R(SoC, T)` and a one-RC model to public cell discharge data and rerun; use the closed form as a control variate for a full electro-thermal twin (`twin-control-variate` style); couple to `uav-energy-twin`'s speed and wind model for a joint endurance twin; estimate `R` online from voltage sag in flight and quantify the information in one hover.

## References
- Chen, M., and Rincón-Mon, G. A. (2006). Accurate electrical battery model capable of predicting runtime and I–V performance. *IEEE Transactions on Energy Conversion* 21(2), 504–511.
- Plett, G. L. (2015). *Battery Management Systems, Volume I: Battery Modeling*. Artech House.
- Leishman, J. G. (2006). *Principles of Helicopter Aerodynamics*, 2nd ed. Cambridge University Press.
