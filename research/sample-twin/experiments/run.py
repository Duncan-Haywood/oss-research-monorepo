"""Reproduces every number in paper/whitepaper.md. Run: PYTHONPATH=src python3 experiments/run.py > experiments/results.txt"""
import cmath
import math
import random
from sample_twin.model import (gains, multipliers, spectral_radius, real_stable, eps_limit, mechanism,
                               hunt_angle, deadbeat_gains, step, step_rk4, twin_step, twin_overshoot, overshoot)

print("Sample twin: unit mass, PD control sampled every T and held (ZOH), kp = wn^2, kd = 2 zeta wn. Twin: continuous control.")
print("eps = wn T.  Real loop stable iff kp T/2 < kd < 2/T, i.e. eps < min(4 zeta, 1/zeta).  T = 1 throughout unless stated (time scaling).")

print("\n== 1. Closed-form window vs multipliers vs an independent RK4 simulation ==")
bad = n = 0
for zeta in (0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 2.0, 5.0):
    for f in (0.5, 0.9, 0.99, 1.01, 1.1, 2.0):
        kp, kd = gains(f * eps_limit(zeta), zeta)
        n += 1
        bad += real_stable(kp, kd, 1.0) != (spectral_radius(kp, kd, 1.0) < 1)
print("window disagrees with multiplier moduli in %d of %d (zeta, eps/eps_limit) cases" % (bad, n))
worst = 0.0
for zeta, eps in ((0.3, 0.6), (0.7, 1.0), (1.0, 0.5), (0.2, 0.7), (2.0, 0.2)):
    kp, kd = gains(eps, zeta)
    a = step(kp, kd, 1.0, 1.0, 40)
    b = step_rk4(kp, kd, 1.0, 1.0, 40, sub=200)
    worst = max(worst, max(abs(p - q) for p, q in zip(a, b)))
print("max |exact ZOH discretisation - RK4 of the continuous plant| over 5 cases x 40 samples = %.2e" % worst)
print("\nzeta   eps_limit   mechanism     spectral radius at 0.9 lim   at 1.1 lim")
for zeta in (0.1, 0.3, 0.5, 0.7, 1.0, 2.0, 5.0):
    L = eps_limit(zeta)
    print("%-6g %-11.5f %-13s %-28.5f %.5f" % (zeta, L, mechanism(zeta), spectral_radius(*gains(0.9 * L, zeta), 1.0),
                                               spectral_radius(*gains(1.1 * L, zeta), 1.0)))

print("\n== 2. A hard cap for every damping: wn T < 2 (kp T^2 < 4); random search ==")
random.seed(0)
stable_below = stable_above = tot_below = tot_above = 0
for _ in range(200000):
    kp = math.exp(random.uniform(-4, 4))
    kd = math.exp(random.uniform(-4, 4))
    s = spectral_radius(kp, kd, 1.0) < 1
    if kp < 4.0:
        tot_below += 1
        stable_below += s
    else:
        tot_above += 1
        stable_above += s
print("kp T^2 < 4: %d stable of %d draws; kp T^2 >= 4: %d stable of %d draws" % (stable_below, tot_below, stable_above, tot_above))
print("cap in frequency: wn < 2/T = omega_s / pi (omega_s = 2 pi / T); f_n < f_s / pi = 0.318 f_s; attained only at zeta = 1/2")

print("\n== 3. Two different failure mechanisms ==")
print("delay branch (zeta < 1/2): boundary kd = kp T/2, pair on the unit circle at angle 2 asin(eps/2) per sample (twin: eps)")
print("zeta  eps=4 zeta   |z|         arg z (rad)   2 asin(eps/2)   twin wn T   hunt freq / twin wn")
for zeta in (0.1, 0.2, 0.3, 0.4):
    eps = 4 * zeta
    kp = eps * eps
    kd = kp / 2.0                      # = 2 zeta wn with zeta = eps/4
    z = multipliers(kp, kd, 1.0)[0]
    th = abs(cmath.phase(z))
    print("%-5g %-10.3f %-11.9f %-13.9f %-15.9f %-11.3f %.4f" % (zeta, eps, abs(z), th, hunt_angle(eps), eps, th / eps))
print("derivative branch (zeta > 1/2): boundary kd T = 2, real multiplier -1 (period-2 chatter at the Nyquist rate), twin never oscillates there")
print("zeta  eps=1/zeta  multipliers")
for zeta in (0.6, 1.0, 2.0, 5.0):
    eps = 1 / zeta
    kp, kd = gains(eps, zeta)
    m = multipliers(kp, kd, 1.0)
    print("%-5g %-11.4f %s" % (zeta, eps, ", ".join("%.6f%+.1ej" % (z.real, z.imag) for z in m)))
kp, kd = gains(0.6, 0.3)
print("delay heuristic: ZOH ~ lag T/2 gives T* = 2 kd/kp, the Routh limit of lag-twin (tau* = kd/kp) with tau = T/2")
print("zeta=0.3, wn=0.6: lag-twin tau* = kd/kp = %.6f, so T* = 2 tau* = %.6f; exact sampled boundary kd = kp T/2 gives T = %.6f" % (
    kd / kp, 2 * kd / kp, 2 * kd / kp))

print("\n== 4. Step response at the sample times (x0 = 1), zeta = 0.7, real vs twin ==")
print("eps   spectral radius   twin per-step factor exp(-zeta eps)   real overshoot   twin overshoot   RMS(real-twin) over 40 steps")
for eps in (0.05, 0.1, 0.3, 0.5, 0.8, 1.0, 1.2, 1.4, 1.42):
    kp, kd = gains(eps, 0.7)
    xs = step(kp, kd, 1.0, 1.0, 4000)
    ref = twin_step(eps, 0.7, 1.0, 1.0, 4000)
    rms = math.sqrt(sum((a - b) ** 2 for a, b in zip(xs[:40], ref[:40])) / 40)
    print("%-5g %-17.5f %-37.5f %-16.4f %-16.4f %.5f" % (eps, spectral_radius(kp, kd, 1.0), math.exp(-0.7 * eps),
                                                        overshoot(xs, 1.0), twin_overshoot(0.7), rms))

print("\n== 5. Twin validated on a gentle test still hides the cliff (zeta = 0.7, wn = 1, horizon 40 time units) ==")
print("T = eps   RMS(real - twin) at the sample times   RMS/eps")
for eps in (0.01, 0.02, 0.05, 0.1, 0.2, 0.5):
    n = int(round(40 / eps))
    kp, kd = gains(1.0, 0.7)
    xs = step(kp, kd, eps, 1.0, n)
    ref = twin_step(1.0, 0.7, eps, 1.0, n)
    rms = math.sqrt(sum((a - b) ** 2 for a, b in zip(xs, ref)) / n)
    print("%-9g %-38.6f %.4f" % (eps, rms, rms / eps))

print("\n== 6. Faster is not better: spectral radius vs eps (T = 1) and the deadbeat point ==")
print("the twin promises per-step factor exp(-zeta eps), falling forever; the real radius bottoms out and rises")
print("zeta   best eps   min radius   twin exp(-zeta eps) there   eps where real radius = 1")
for zeta in (0.3, 0.5, 0.6, 0.7, 0.75, 0.9, 1.0, 1.5):
    best = (9, 0)
    for k in range(1, 40000):
        eps = k * 1e-4 * eps_limit(zeta)
        r = spectral_radius(*gains(eps, zeta), 1.0)
        if r < best[0]:
            best = (r, eps)
    print("%-6g %-10.4f %-12.6f %-27.5f %.4f" % (zeta, best[1], best[0], math.exp(-zeta * best[1]), eps_limit(zeta)))
kp, kd = deadbeat_gains(1.0)
print("deadbeat gains kp T^2 = %.3f, kd T = %.3f (eps = 1, zeta = 0.75): multipliers %s; x_k = %s" % (
    kp, kd, multipliers(kp, kd, 1.0), ["%.3g" % x for x in step(kp, kd, 1.0, 1.0, 4)]))
print("twin with the same gains: per-step factor exp(-0.75) = %.4f, x(T), x(2T), x(3T) = %s" % (
    math.exp(-0.75), ["%.4f" % x for x in twin_step(1.0, 0.75, 1.0, 1.0, 3)]))
x, v = 1.0, 0.0
worst = 0.0
for k in range(4):
    u = -kp * x - kd * v
    for j in range(1, 1001):
        t = j / 1000.0
        worst = min(worst, x + v * t + u * t * t / 2)
    x, v = x + v + u / 2, v + u
print("intersample: most negative x(t) of the deadbeat loop over 4 periods = %.5f (twin overshoot at zeta = 0.75: %.5f)" % (
    worst, twin_overshoot(0.75)))

print("\n== 7. Design rule: margin m = eps / eps_limit, so wn <= m min(4 zeta, 1/zeta) / T ==")
print("zeta = 0.7, T = 0.01 s (asymptotic, from the spectral radius):")
print("                          m     wn_max (rad/s)  spectral radius   real steps to 1e-6   twin time to 1e-6 (s)   (real steps x T)")
for m in (1.0, 0.75, 0.5, 0.25, 0.1):
    T = 0.01
    wn = m * eps_limit(0.7) / T
    r = spectral_radius(*gains(wn, 0.7), T)
    steps = math.log(1e-6) / math.log(r) if r < 1 else float('inf')
    print("                          %-5g %-15.2f %-16.5f %-15.1f %.3f  (%.3f)" % (m, wn, r, steps, -math.log(1e-6) / (0.7 * wn), steps * T))

print("\n== 8. Twin control rate vs real control rate (zeta = 0.7) ==")
print("wn (rad/s)   stable at T = 1 ms?   stable at T = 10 ms?   limit T for this wn (ms)")
for wn in (10.0, 30.0, 60.0, 100.0, 142.0, 150.0, 300.0):
    kp, kd = gains(wn, 0.7)
    print("%-12g %-21s %-22s %.3f" % (wn, real_stable(kp, kd, 0.001), real_stable(kp, kd, 0.01), 1000 * eps_limit(0.7) / wn))
