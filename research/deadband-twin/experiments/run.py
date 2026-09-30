"""Reproduces every number in paper/whitepaper.md. Run: PYTHONPATH=src python3 experiments/run.py > experiments/results.txt"""
import math, random
from deadband_twin.model import *

G, DELTA, SW = 1.0, 0.5, 0.1
print("Deadband twin: real y = g D(u) + w, deadband delta=%.1f, g=%.1f, sw=%.2f; twin is linear y = b u fitted by OLS." % (DELTA, G, SW))

print("\n== 0. Fitted gain = P(|z| > delta/s) (n=200000, s=1) ==")
print("delta   law 2Q(d)   simulated b   R2 linear fit   R2 (g D(u) model)   corr(resid,u)")
rng = random.Random(7)
for dl in (0.0, 0.25, 0.5, 1.0, 1.5, 2.0):
    u, y = simulate(200000, G, dl, 1.0, SW, rng)
    b = ols(u, y)
    z = [dead(t, dl) for t in u]
    gh = ols(z, y) if dl > 0 else b
    my, mu = sum(y) / len(y), sum(u) / len(u)
    mz = sum(z) / len(z)
    e = [(t - my) - b * (s - mu) for s, t in zip(u, y)]
    print("%-7g %-11.4f %-13.4f %-15.3f %-19.3f %.1e" % (dl, plim_gain(G, dl, 1.0), b, r2_line(u, y, b),
          1 - sum((t - my - gh * (dead(s, dl) - mz)) ** 2 for s, t in zip(u, y)) / sum((t - my) ** 2 for t in y),
          cov(u, e) / math.sqrt(cov(u, u) * cov(e, e))))

print("\n== 1. Twin fitted at s=1 (n=200000), deployed at other excitation scales s (delta=0.5) ==")
rng = random.Random(11)
u, y = simulate(200000, G, DELTA, 1.0, SW, rng)
b = ols(u, y)
print("fitted twin gain b = %.4f (law %.4f)" % (b, plim_gain(G, DELTA, 1.0)))
print("s      real gain 2Q(d/s)   twin/real   held-out R2 of twin   RMSE twin / sd(y)")
for s in (0.1, 0.25, 0.5, 1.0, 2.0, 4.0):
    u2, y2 = simulate(100000, G, DELTA, s, SW, rng)
    my = sum(y2) / len(y2)
    sd = math.sqrt(sum((t - my) ** 2 for t in y2) / len(y2))
    mse = sum((t - b * s_) ** 2 for s_, t in zip(u2, y2)) / len(y2)
    real = plim_gain(G, DELTA, s)
    print("%-6g %-19.4f %-11.3f %-21.3f %.3f" % (s, real, b / real if real > 1e-9 else float("inf"), 1 - mse / (sd * sd), math.sqrt(mse) / sd))

print("\n== 2. Feedforward u = r/b with the twin gain b (s=1 fit), real output D(u) ==")
b1 = plim_gain(G, DELTA, 1.0)
print("twin b = %.4f (exact law); commands below delta*b = %.3f produce exactly zero output" % (b1, DELTA * b1))
print("target r   command u   real output / target")
for r in (0.1, 0.2, 0.3, 0.5, 1.0, 2.0, 5.0):
    uu = r / b1
    print("%-10g %-11.3f %.3f" % (r, uu, dead(uu, DELTA) / r))

print("\n== 3. Closed-loop stall: x <- x + D(k (r-x)); twin predicts error -> 0 for any 0<k<2 ==")
print("k     delta/k   max |final error| over e0 in (0,5]   attained at e0")
for k in (0.25, 0.5, 1.0, 1.5, 1.9):
    best, arg = 0.0, 0.0
    for i in range(1, 501):
        e0 = i * 0.01
        f = abs(stall_error(e0, k, DELTA))
        if f > best + 1e-12:
            best, arg = f, e0
    print("%-5g %-9.3f %-36.3f %.2f" % (k, DELTA / k, best, arg))
print("k=1 (deadbeat in the twin): final |e| = min(|e0|, delta) exactly: e0=0.3 -> %.3f, 0.5 -> %.3f, 2.0 -> %.3f" % (
    abs(stall_error(0.3, 1.0, DELTA)), abs(stall_error(0.5, 1.0, DELTA)), abs(stall_error(2.0, 1.0, DELTA))))

print("\n== 4. Repair: fit (g, delta) instead of one gain (train s=1; 300 repeats) ==")
print("n      mean g   sd g    mean delta   sd delta   RMSE at s=0.25: linear twin   deadband twin   (RMSE / sd(y))")
for n in (100, 300, 1000):
    rng = random.Random(500 + n)
    gs, ds, el, ed = [], [], [], []
    u2, y2 = simulate(50000, G, DELTA, 0.25, SW, random.Random(9))
    my = sum(y2) / len(y2)
    sd = math.sqrt(sum((t - my) ** 2 for t in y2) / len(y2))
    for _ in range(300):
        u, y = simulate(n, G, DELTA, 1.0, SW, rng)
        bb = ols(u, y)
        gh, dh = fit_deadband(u, y)
        gs.append(gh); ds.append(dh)
        el.append(math.sqrt(sum((t - bb * s_) ** 2 for s_, t in zip(u2[:2000], y2[:2000])) / 2000) / sd)
        ed.append(math.sqrt(sum((t - gh * dead(s_, dh)) ** 2 for s_, t in zip(u2[:2000], y2[:2000])) / 2000) / sd)
    m = lambda v: sum(v) / len(v)
    sdv = lambda v: math.sqrt(sum((t - m(v)) ** 2 for t in v) / (len(v) - 1))
    print("%-6d %-8.3f %-7.3f %-12.3f %-10.3f %-28.3f %.3f" % (n, m(gs), sdv(gs), m(ds), sdv(ds), m(el), m(ed)))
