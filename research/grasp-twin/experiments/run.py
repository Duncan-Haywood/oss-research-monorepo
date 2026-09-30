"""Reproduces every number in paper/whitepaper.md. Run: PYTHONPATH=src python3 experiments/run.py > experiments/results.txt"""
import math
from grasp_twin import *

M, A = 0.5, 3.0
L = load(M, A)
MU0, S, CD, CF = 0.5, 0.35, 1.0, 0.01
N0 = L / (2 * MU0)
Nstar, Jstar = best_force(L, MU0, S, CD, CF)
zs = z_star(N0, S, CD, CF)
print("Grasp: m=%g kg lifted at a=%g m/s^2, load L=m(g+a)=%.3f N, two contacts. Real friction lognormal(median %g, log-sd %g)." % (M, A, L, MU0, S))
print("Cost J(N) = c_d P(slip) + c_f N with c_d=%g, c_f=%g per N; N0=L/(2 mu0)=%.3f N (grip force at the median slip threshold), c_f N0/c_d=%.3f." % (CD, CF, N0, CF * N0 / CD))

print("\n== 1. Closed-form optimum vs grid, and drop rate vs a time-stepped Coulomb simulation ==")
zb, jb = brute_force_z(N0, S, CD, CF)
print("closed form z*=%.4f N*=%.3f J*=%.5f P(slip)=Phi(z*)=%.4f ; grid z=%.4f J=%.5f" % (zs, Nstar, Jstar, Phi(zs), zb, jb))
print("no-grip corner costs c_d=%g; N* is interior and %.1f%% above the median-threshold force N0." % (CD, 100 * (Nstar / N0 - 1)))
thr = L / (2 * 0.6)
print("dynamic sim threshold check (mu=0.6, static threshold %.4f N): holds at 1.01x: %s, slips at 0.99x: %s" % (thr, not simulate_grasp(1.01 * thr, 0.6, M, A), simulate_grasp(0.99 * thr, 0.6, M, A)))
for N, lab in ((Nstar, "N*"), (N0, "N0"), (1.2 * N0, "1.2 N0")):
    print("N=%-7s %.3f  closed-form drop %.4f  simulated (20000 grasps) %.4f" % (lab, N, real_drop(N, L, MU0, S), simulate_drop_rate(N, M, A, MU0, S, 20000, seed=5)))

print("\n== 2. Deterministic-friction twin (s_twin = 0): corner theorem ==")
print("The twin's optimiser grips exactly at its own slip threshold N=L/(2 mu_twin) (when c_d > c_f N), so real drop prob = Phi(b/s), b = ln(mu_twin/mu0).")
print("b       mu_twin   N_twin   real drop  Phi(b/s)  real cost  regret  regret/J*")
for b in (-0.4, -0.2, 0.0, 0.2, 0.4, 0.6):
    mt = MU0 * math.exp(b)
    N = twin_force(L, mt, 0.0, CD, CF)
    c = real_cost(N, L, MU0, S, CD, CF)
    print("%-6g  %.3f     %.3f    %.4f     %.4f    %.4f     %.4f  %.1f%%" % (b, mt, N, real_drop(N, L, MU0, S), Phi(b / S), c, c - Jstar, 100 * (c - Jstar) / Jstar))
mean_t = MU0 * math.exp(S * S / 2)
print("twin friction = real MEAN (%.4f): real drop %.4f = Phi(s/2) = %.4f; = real median: %.4f" % (mean_t, real_drop(twin_force(L, mean_t, 0.0, CD, CF), L, MU0, S), Phi(S / 2), real_drop(twin_force(L, MU0, 0.0, CD, CF), L, MU0, S)))
print("s (real log-sd)  drop at mean-matched twin Phi(s/2)")
for s in (0.1, 0.2, 0.35, 0.5, 0.8):
    print("%-6g  %.4f" % (s, Phi(s / 2)))

print("\n== 3. Randomised-friction twin (width s_twin), real drop = Phi((b + s_twin z_T)/s) ==")
for b in (0.0, 0.4):
    mt = MU0 * math.exp(b)
    print("twin bias b=%g (twin friction %.3f vs real median %.3f):" % (b, mt, MU0))
    print("  s_twin  N_twin   real drop  formula   regret   regret/J*")
    best = None
    for st in (0.0, 0.05, 0.1, 0.2, 0.35, 0.5, 0.7, 1.0):
        N = twin_force(L, mt, st, CD, CF)
        z = z_star(L / (2 * mt), st, CD, CF) if st > 0 else None
        f = Phi((b + st * z) / S) if z is not None else float('nan')
        r = regret(L, MU0, S, CD, CF, mt, st)
        print("  %-6g  %.3f    %.4f     %.4f    %.4f   %.1f%%" % (st, N, real_drop(N, L, MU0, S), f, r, 100 * r / Jstar))
    grid = [i / 1000 for i in range(0, 1501)]
    bs = min(grid, key=lambda st: regret(L, MU0, S, CD, CF, mt, st))
    print("  best width by grid: s_twin=%.3f regret %.5f (%.2f%% of J*), real drop %.4f" % (bs, regret(L, MU0, S, CD, CF, mt, bs), 100 * regret(L, MU0, S, CD, CF, mt, bs) / Jstar, real_drop(twin_force(L, mt, bs, CD, CF), L, MU0, S)))

print("\n== 4. A safety factor k on the deterministic twin's force: real drop = Phi((b - ln k)/s), needed ln k = b + s*z(1-delta) ==")
print("delta=0.01 target, z_(1-delta)=%.4f" % (-Phi_inv(0.01)))
print("b      s      k needed   k=1.5 drop  k=2 drop")
for b in (0.0, 0.4):
    for s in (0.2, 0.35, 0.5, 0.8):
        k = math.exp(b - s * Phi_inv(0.01))
        print("%-5g  %-5g  %-9.2f  %.4f      %.4f" % (b, s, k, Phi((b - math.log(1.5)) / s), Phi((b - math.log(2)) / s)))
print("Cost check at b=0.4,s=%g: k=1.5 real cost %.4f, k=2 %.4f, k for 1%% drop (%.2f) %.4f, real optimum %.4f" % (S, real_cost(1.5 * twin_force(L, MU0 * math.exp(0.4), 0.0, CD, CF), L, MU0, S, CD, CF),
      real_cost(2 * twin_force(L, MU0 * math.exp(0.4), 0.0, CD, CF), L, MU0, S, CD, CF), math.exp(0.4 - S * Phi_inv(0.01)),
      real_cost(math.exp(0.4 - S * Phi_inv(0.01)) * twin_force(L, MU0 * math.exp(0.4), 0.0, CD, CF), L, MU0, S, CD, CF), Jstar))

print("\n== 5. Setting the twin's friction from n real measurements (plug-in quantile of ln mu) ==")
print("Threshold ybar + k*shat on ln mu, so the force is at the estimated delta-quantile of slip threshold; exact expected drop = E Phi(k shat/s / sqrt(1+1/n)).")
for delta in (0.01, 0.05):
    z = Phi_inv(delta)
    print("target delta=%g (z=%.4f)" % (delta, z))
    print("  n     plug-in exact  Monte Carlo  2nd-order   inflation  corrected k_n  check")
    for n in (5, 10, 20, 50, 100, 500):
        ex = predictive_drop(n, z)
        mc = sample_plugin_drop(n, z, 40000 if n < 100 else 10000, seed=n)
        kn = plugin_multiplier(n, delta)
        print("  %-5d %.4f         %.4f       %.4f      %.2fx      %.3f (vs %.3f)  %.4f" % (n, ex, mc, delta_predictive_drop(n, delta), ex / delta, kn, z, predictive_drop(n, kn)))
    # smallest n with inflation <= 1.25x
    n = 3
    while predictive_drop(n, z) > 1.25 * delta: n += 1
    print("  smallest n with plug-in drop <= 1.25*delta: %d" % n)

print("\n== 6. Does the compensating width transfer across tasks? (bias b=0.4, width fitted on the m=0.5 kg grasp) ==")
b = 0.4
mt = MU0 * math.exp(b)
st_fit = min([i / 1000 for i in range(0, 1501)], key=lambda st: regret(L, MU0, S, CD, CF, mt, st))
print("fitted s_twin=%.3f (regret 0 on the m=0.5 kg task by construction)" % st_fit)
print("mass   load    real N*   twin N   real drop  regret   regret/J*   regret of unbiased twin s_twin=%.2f" % S)
for m in (0.1, 0.25, 0.5, 1.0, 2.0, 4.0):
    Lm = load(m, A)
    Ns, Js = best_force(Lm, MU0, S, CD, CF)
    Nt = twin_force(Lm, mt, st_fit, CD, CF)
    r = regret(Lm, MU0, S, CD, CF, mt, st_fit)
    print("%-6g %-7.3f %-9.3f %-8.3f %.4f     %.5f  %.2f%%       %.5f" % (m, Lm, Ns, Nt, real_drop(Nt, Lm, MU0, S), r, 100 * r / Js, regret(Lm, MU0, S, CD, CF, MU0, S)))
