# The twin whose actuator has no dead zone: Bussgang gain, basins of instability, and asymmetric compensation

*Stylised: scalar plant `x' = x + b·D(u)`, `b=1`, `δ=0.1`, symmetric dead zone, Gaussian dither, design fraction `c=0.5`. Pure Python; every number is from `experiments/results.txt` (seeded, ~1 min). The "real" system is itself simulated; no lab or field data. Negative results are reported as such.*

## Question
A twin builder logs a real actuator under random excitation and fits a linear gain. If the actuator has a dead zone, what does the fit recover, what does a controller tuned on it do on the real system, and what does fitting the dead zone explicitly buy?

## Model
Real actuator `D(u)=u−δ sgn u` for `|u|>δ`, else 0; plant `x'=x+b D(u)`; logs `y=b D(u)+w`, `u~N(0,σ²)`. The twin is `x'=x+g u`, `ĝ=Σuy/Σu²`. Since `E[uD(u)]=σ²E[D'(u)]` (Stein), `ĝ→b·P(|u|>δ)=b·erfc(δ/(σ√2))` (Bussgang 1952). Control `u=−Ke`, `K=c/ĝ`, so the twin predicts `e'=(1−c)e`. Real loop gain `m=bK=c/P`. Outside the dead zone `e'=(1−m)e+bδ sgn e`:
- `m<1`: `e_k−δ/K=(1−m)^k(e₀−δ/K)`, monotone from above, never enters the zone; limit `δ/K`.
- `1<m<2`: `|e'|=(m−1)|e|−bδ` contracts until `|e|≤δ/K` and the loop stops.
- `m>2`: same map, repelling magnitude `bδ/(m−2)`; `|e₀|` below it stops inside the zone, above it diverges.
Compensation `u=−Ke−δ̂ sgn e`, `Δ=δ̂−δ`: `Δ<0` gives floor `|Δ|/K`; `Δ>0` keeps `|u|>δ` always, so `e'=(1−m)e−bΔ sgn e`, a 2-cycle of amplitude `bΔ/(2−m)`. (`(b,δ)` fit: for each `δ` on a grid the best `b` is closed-form; pick least SSE.)

## Results
1. **Bussgang law** (n=2·10⁵, no noise): `ĝ/b` simulated 0.0001 / 0.0455 / 0.3176 / 0.6170 / 0.8025 vs `P` = 0.0001 / 0.0455 / 0.3173 / 0.6171 / 0.8026 at σ/δ = 0.25 / 0.5 / 1 / 2 / 4. The twin's gain is an excitation property: identical hardware yields gains from 0 to 0.9·b.
2. **Deploy** (e₀=1, 3000 steps). σ/δ = 0.5: `m`=10.99, diverges. σ/δ = 1: `m`=1.58, stops at |e|=1.3·10⁻⁴ inside the zone. σ/δ = 1.5 / 2 / 4 / 8: `m` = 0.99 / 0.81 / 0.62 / 0.56, final error 0.101 / 0.123 / 0.160 / 0.180, each equal to `δ/K`. The twin predicted 0 in all cases. A twin fitted with small dither (underestimated gain) is dangerous; one fitted with large dither is merely off by a floor. Note that the honest gain `K=c/b` has a *larger* floor (0.200) than any of these, so an underestimated gain "helps" the floor while eroding the stability margin.
3. **Stability is a basin above m=2.** `m`=0.5 / 0.9 → floor 0.200 / 0.111 (= `δ/K`); 1.1 / 1.5 / 1.9 / 1.99 → stops inside the zone (|e| 0 / 0.050 / 0.043 / 0.049, all ≤ `δ/K`); 2.01 / 2.05 with edges 10 / 2 → e₀=1 stops (0.041 / 0.020); 2.2 / 2.5 with edges 0.5 / 0.2 → blows up. At m=2.5, e₀=0.19 settles (0.029) and e₀=0.21 blows up.
4. **Compensation is asymmetric** (K=c/b, m=0.5, deterministic, matches formulas to 6 digits). `Δ/δ` = −0.5 / −0.25 / −0.1 → floor 0.100 / 0.050 / 0.020; +0.1 / +0.25 / +0.5 → 2-cycle 0.0067 / 0.0167 / 0.0333. For the same `|Δ|`, under-compensation costs `(2−m)/m = 3×` more error at m=0.5, but over-compensation never settles (a permanent chatter).
5. **Fitting (b,δ)** (σ=1.5δ, noise 0.02, 300 repeats). n = 100 / 400 / 1600: `δ̂` RMSE/δ 0.049 / 0.025 / 0.008; `P(δ̂>δ)` 0.28 / 0.14 / 0.01; `b̂` RMSE/b 0.040 / 0.022 / 0.008; mean real final |e| with the fitted compensation 0.0046 / 0.0016 / 0.0001, against 0.079 / 0.090 / 0.097 for the single-gain OLS twin (mean OLS `ĝ/b`≈0.50, equal to `P` at σ=1.5δ) and 0.200 for the honest-gain P loop with no compensation.

## Limitations
Scalar plant, symmetric static dead zone (real actuators have asymmetric zones, hysteresis/backlash, rate limits and stiction, where the Bussgang gain no longer applies); Gaussian i.i.d. dither with noise-free state in the loop, so measurement noise (which changes the regulation floor) is absent; the `δ` grid contains the true value on a 0.005 step, which flatters `δ̂` (the RMSEs of 0.8–5% are therefore optimistic); no closed-loop identification (see `closedloop-twin`); deterministic loop results are exact for this model only. Not a claim about any specific robot.

## Next steps
Asymmetric zones and backlash (hysteresis makes the gain history dependent); dynamics behind the actuator (integral action plus a dead zone gives hunting limit cycles); grid-free estimators with proper uncertainty on `δ`; choosing the identification amplitude to match the operating amplitude; a certificate that flags a fitted linear gain as excitation-dependent.

## References
- Bussgang, J. J. (1952). Crosscorrelation functions of amplitude-distorted Gaussian signals. *MIT RLE Tech. Rep. 216*.
- Stein, C. M. (1981). Estimation of the mean of a multivariate normal distribution. *Annals of Statistics* 9(6).
- Tao, G. & Kokotović, P. V. (1996). *Adaptive Control of Systems with Actuator and Sensor Nonlinearities*. Wiley.
- Zhao, W., Queralta, J. P. & Westerlund, T. (2020). Sim-to-real transfer in deep reinforcement learning for robotics: a survey. *IEEE SSCI*.
