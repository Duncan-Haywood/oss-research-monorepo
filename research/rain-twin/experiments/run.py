"""Reproduces every number in paper/whitepaper.md. Run: PYTHONPATH=src python3 experiments/run.py > experiments/results.txt"""
import math
import random
from rain_twin.model import (lambertw, kappa, rain_rate, detect, r_d, kappa_star, p_detect, quantile_range, mean_range, mean_rain,
                             sample_rain, brier_deterministic, brier_calibrated)

R0, K, ALPHA, P, M = 20.0, 0.05, 1.0, 0.10, 8.0   # clear-air range 20 km; gamma = 0.05 R dB/km one way; rain 10% of the time, mean 8 mm/h when raining

print("Rain twin: detect iff 4 ln(r0/r) >= 2 kappa r; r0=%g km, gamma=%g R^%g dB/km, P(rain)=%g, mean rain rate when raining %g mm/h" % (R0, K, ALPHA, P, M))

print("\n== 1. Detection range (exact, Lambert W) ==")
print("   R(mm/h)  kappa(Np/km)  r_d(km)   residual r - r0 exp(-kappa r/2)   detect(0.999 r_d) detect(1.001 r_d)")
for R in (0, 1, 5, 10, 30, 60):
    kap = kappa(R, K, ALPHA)
    rd = r_d(kap, R0)
    print("   %5.1f     %.5f     %6.3f    %.2e                         %s %s" % (R, kap, rd, rd - R0 * math.exp(-kap * rd / 2),
                                                                               detect(0.999 * rd, kap, R0), detect(1.001 * rd, kap, R0)))

print("\n== 2. Convexity and the Jensen gap: mean range vs range at mean rain ==")
rng = random.Random(1)
N = 400000
draws = [sample_rain(rng, P, M) for _ in range(N)]
mc_mean = sum(r_d(kappa(R, K, ALPHA), R0) for R in draws) / N
exact = mean_range(R0, K, ALPHA, P, M)
Rbar = mean_rain(P, M)
print("mean rain rate p*m = %.2f mm/h; mean-rain twin range r_d(kappa(p m)) = %.3f km" % (Rbar, r_d(kappa(Rbar, K, ALPHA), R0)))
print("real mean range E[r_d]: quadrature %.3f km, Monte Carlo (%d draws) %.3f km; Jensen gap = %.3f km" % (
    exact, N, mc_mean, exact - r_d(kappa(Rbar, K, ALPHA), R0)))
xs = [0.1 * i for i in range(1, 300)]
second = [r_d(2 * (x + 0.01) / R0, R0) - 2 * r_d(2 * x / R0, R0) + r_d(2 * (x - 0.01) / R0, R0) for x in xs]
print("second difference of r_d in kappa over x = kappa r0/2 in (0.1, 29.9): min %.3e (>0 => convex)" % min(second))
for alpha in (0.7, 1.0, 1.3):
    kk = 0.05
    ex = mean_range(R0, kk, alpha, P, M, n=50000)
    print("   alpha=%.1f: E[r_d] %.3f, r_d(kappa(pm)) %.3f, gap %.3f" % (alpha, ex, r_d(kappa(P * M, kk, alpha), R0),
                                                                    ex - r_d(kappa(P * M, kk, alpha), R0)))

print("\n== 3. Detection probability versus range (closed form vs Monte Carlo, 200000 draws) ==")
print("   r(km)  P_real closed   P_real MC   clear-air twin   mean-rain twin")
rm = r_d(kappa(Rbar, K, ALPHA), R0)
rng = random.Random(2)
dr = [sample_rain(rng, P, M) for _ in range(200000)]
for r in (4, 8, 12, 14, 16, 18, 19, 19.9):
    pc = p_detect(r, R0, K, ALPHA, P, M)
    mc = sum(detect(r, kappa(R, K, ALPHA), R0) for R in dr) / len(dr)
    print("   %5.1f   %.4f        %.4f      %d                %d" % (r, pc, mc, r <= R0, r <= rm))
print("P(detect) for r<=r0 is bounded below by 1-p = %.2f: at r=4 km it is %.4f" % (1 - P, p_detect(4, R0, K, ALPHA, P, M)))

print("\n== 4. Quantile equivariance: the median-rain twin matches the median range, the mean-rain twin does not ==")
print("(for monotone r_d, the q-quantile of rain maps to the (1-q)-quantile of range; the mean does not commute)")
for pp in (0.1, 0.4, 0.6, 0.8):
    mdn_R = -M * math.log(0.5 / pp) if pp > 0.5 else 0.0     # median of rain mixture: P(R>x)=p exp(-x/m)=0.5
    med_range = quantile_range(0.5, R0, K, ALPHA, pp, M)
    med_twin = r_d(kappa(mdn_R, K, ALPHA), R0)
    mean_twin = r_d(kappa(pp * M, K, ALPHA), R0)
    print("   p=%.1f: median range (real) %.3f, median-rain twin %.3f, mean-rain twin %.3f, E[r_d] %.3f" % (
        pp, med_range, med_twin, mean_twin, mean_range(R0, K, ALPHA, pp, M, n=50000)))

print("\n== 5. Brier against real outcomes, ranges uniform on 2-20 km (excess = Brier - irreducible mean P(1-P)) ==")
rs = [2 + 18 * (i + 0.5) / 4000 for i in range(4000)]
irr = brier_calibrated(rs, R0, K, ALPHA, P, M, P, M)
print("irreducible (calibrated, true climatology): %.4f" % irr)
print("   twin                                    range/params     Brier    excess")
cands = [("clear-air (R=0) deterministic", R0), ("mean-rain deterministic", rm),
         ("median-matched deterministic (0.5 quantile)", quantile_range(0.5, R0, K, ALPHA, P, M)),
         ("calibrated-to-mean-range deterministic", mean_range(R0, K, ALPHA, P, M, n=50000))]
for name, rt in cands:
    b = brier_deterministic(rs, R0, K, ALPHA, P, M, rt)
    print("   %-44s %6.3f km   %.4f   %.4f" % (name, rt, b, b - irr))
print("   climatology ensembles: twin (p_t, m_t) vs real (%.2f, %.1f)" % (P, M))
for pt, mt in ((P, M), (0.05, M), (0.2, M), (P, 4.0), (P, 16.0), (0.01, M), (0.5, M)):
    b = brier_calibrated(rs, R0, K, ALPHA, P, M, pt, mt)
    print("      p_t=%.2f m_t=%4.1f                      %.4f   %.4f" % (pt, mt, b, b - irr))

print("\n== 6. Frequency proxy: scale k (dB/km per mm/h) ==")
print("   k      r_d(mean rain)  E[r_d]   gap     clear-air Brier excess  mean-rain Brier excess")
for kk in (0.01, 0.02, 0.05, 0.1, 0.3):
    rmk = r_d(kappa(Rbar, kk, ALPHA), R0)
    ek = mean_range(R0, kk, ALPHA, P, M, n=50000)
    i0 = brier_calibrated(rs, R0, kk, ALPHA, P, M, P, M)
    print("   %.2f   %7.3f        %7.3f  %6.3f   %.4f                  %.4f" % (
        kk, rmk, ek, ek - rmk, brier_deterministic(rs, R0, kk, ALPHA, P, M, R0) - i0,
        brier_deterministic(rs, R0, kk, ALPHA, P, M, rmk) - i0))
