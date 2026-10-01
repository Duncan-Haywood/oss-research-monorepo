# A twin run at the mean rain rate is the wrong twin: radar detection range under intermittent rain attenuation

## Question
Simulators often fold weather into a radar model as a single "average rain" parameter. Detection range is a nonlinear function of attenuation and rain is intermittent, so which scalar summary of the rain climatology should a deterministic twin use, and how much does the summary matter compared with running a rain ensemble?

## Model
Real: free-space clear-air range `r0`. One-way specific attenuation `γ = kR^α` dB/km; `κ = (ln 10/10)γ` nepers (power)/km. Two-way power factor `e^{−2κr}`, free-space SNR `∝ r^{−4}`, so the target is detected iff `4 ln(r0/r) ≥ 2κr`; the left side minus the right is decreasing in `r`, so detection holds exactly for `r ≤ r_d(κ)`, the root of `r = r0 e^{−κr/2}`, i.e. `r_d = (2/κ) W(κ r0/2)`. Rain rate `R` is 0 with probability `1−p` and exponential with mean `m` otherwise. Parameters: `r0 = 20 km`, `k = 0.05`, `α = 1`, `p = 0.1`, `m = 8 mm/h` (illustrative).
Detection at range `r < r0` needs `κ ≤ κ*(r) = 2 ln(r0/r)/r`, i.e. `R ≤ R*(r)`, so `P(r) = 1 − p·exp(−R*(r)/m)`. Twins: clear air (`R = 0`); mean rain (`R = pm`); median-matched (`r_twin` = range with `P = ½`); calibrated to the real mean range (`r_twin = E[r_d]`); a climatology ensemble with parameters `(p_t, m_t)` reporting `Q(r) = 1 − p_t exp(−R*(r)/m_t)`. Brier is evaluated against the real outcome probabilities `P(r)` with ranges uniform on 2–20 km; since the Brier rule is proper, the excess over the irreducible `∫P(1−P)` is exactly `∫(Q−P)²` (for a deterministic twin, `Q ∈ {0,1}`).

## Results
(all numbers from `experiments/results.txt`)
1. **Detection range.** `r_d` = 20.000, 18.028, 13.544, 10.763, 6.504, 4.390 km at `R` = 0, 1, 5, 10, 30, 60 mm/h; fixed-point residual ≤ 4e-15; detection flips exactly at `r_d`. A second difference over `κr0/2 ∈ (0.1, 29.9)` is positive everywhere on the grid (min 2.2e-7), so `r_d` is convex in `κ`.
2. **Jensen gap.** Mean rain `pm = 0.8 mm/h` gives `r_d = 18.377 km`; the real mean range is 19.320 km (quadrature) / 19.323 km (400,000 draws): the mean-rain twin under-predicts by 0.943 km. The gap is 1.222 / 0.943 / 0.673 km for `α` = 0.7 / 1.0 / 1.3, and rises with `k`: 0.103, 0.289, 0.943, 1.999, 5.028 km at `k` = 0.01, 0.02, 0.05, 0.1, 0.3. I report convexity in `κ` only; the sign for general `α` in the rain-rate variable was checked at these three values only.
3. **Detection probability.** Closed form vs Monte Carlo (200,000 draws): 1.0000/1.0000 at 4 km, 0.9603/0.9613 at 12 km, 0.9057/0.9070 at 19 km, 0.9005/0.9017 at 19.9 km. For any `r < r0`, `P ≥ 1−p`: rain never removes more than `p` of the probability mass.
4. **Quantiles versus means.** For `p` = 0.1, 0.4, 0.6, 0.8 the real median range is 20.000, 20.000, 17.297, 14.586 km; the median-rain twin matches to all printed digits, the mean-rain twin gives 18.377, 15.134, 13.698, 12.581 km and `E[r_d]` is 19.320, 17.280, 15.920, 14.560 km. A monotone map commutes with quantiles, not with expectations.
5. **Scores.** Irreducible Brier 0.0352. Excess: clear-air 0.0026, median-matched 0.0026 (it coincides with clear air at `p = 0.1`, since `P ≥ 0.9` everywhere), mean-rain 0.0756, calibrated-to-mean-range 0.0330. Climatology ensembles: true `(p, m)` 0.0000; `p_t` = 0.05 / 0.2 / 0.01 / 0.5: 0.0007 / 0.0026 / 0.0021 / 0.0417; `m_t` = 4 / 16: 0.0002 / 0.0002. The mean-rain twin's excess rises with attenuation (0.0170 to 0.2886 for `k` = 0.01 to 0.3) while the clear-air twin's rises more slowly (0.0008 to 0.0058).

## Interpretation
The mean rain rate is a poor summary twice over: attenuation is a convex-range transformation (Jensen), and intermittency means the mean describes neither the clear (90%) nor the rainy state. Quantile summaries are equivariant and the climatology ensemble is calibrated by construction. Where rain is rare, the clear-air twin is close to the best deterministic one; the penalty for ignoring rain shows up in the tail (rare but severe), which Brier at a uniform range grid under-weights.

## Limitations
Stylised, no radar or rain-gauge data. Single rain rate over the whole path; real rain cells are spatially patchy and path-integrated attenuation differs from `κr`. Exponential rain rates (measured distributions are heavier-tailed, e.g. lognormal-like). No rain backscatter clutter, noise or Swerling fluctuation: detection is a hard threshold, so all uncertainty comes from the rain climatology. `k`, `α` are illustrative. One clear-air range and one `(p, m)` for most results; Monte Carlo uses one seed per check.

## Next steps
Spatial rain cells and path-integrated attenuation; heavy-tailed rain rates; fitting `(p, m)` from logged detection ranges and the cost of the fit (`twin-recalibration`); rain backscatter as a competing effect (`radar-clutter-twin`); weather-conditioned certification of a UAV sensing twin (`twin-certification`).

## References
- Skolnik, M. I. (2008). *Radar Handbook*, 3rd ed. McGraw-Hill.
- Marshall, J. S. & Palmer, W. M. K. (1948). The distribution of raindrops with size. *Journal of Meteorology* 5(4).
- ITU-R Recommendation P.838. Specific attenuation model for rain for use in prediction methods.
- Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. *Monthly Weather Review* 78(1).
- Corless, R. M., Gonnet, G. H., Hare, D. E. G., Jeffrey, D. J. & Knuth, D. E. (1996). On the Lambert W function. *Advances in Computational Mathematics* 5.
