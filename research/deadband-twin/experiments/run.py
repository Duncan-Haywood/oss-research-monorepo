"""Deadband twin experiments.  Every number in the README / white paper is printed here (seeded)."""
import math
import random

from deadband_twin.model import (deadband, p_active, simulate_id, ols_gain, fit_deadband, loop, floor_p,
                                 chatter_amp, basin_edge)

B, D, SW, C = 1.0, 0.1, 0.02, 0.5   # real gain, real dead zone, log noise, twin's design fraction (twin predicts e'=(1-C)e)


def regime(m, e0=1.0):
    if m < 1:
        return "monotone"
    if m < 2:
        return "alternating"
    return "stops(basin)" if e0 < basin_edge(B, D, m) else "diverges"


def final(tr):
    return tr[-1]


print("== 1. Bussgang law: OLS gain from Gaussian dither is b*P(|u|>d)  (n=200000, sw=0)")
print("sigma/d   P(|u|>d)   simulated g/b")
for r in (0.25, 0.5, 1.0, 2.0, 4.0):
    u, y = simulate_id(200000, B, D, r * D, 0.0, random.Random(10))
    print(f"{r:6.2f}   {p_active(D, r * D):8.4f}   {ols_gain(u, y) / B:8.4f}")

print("\n== 2. Deploy: K = C/g_fit designed in the twin (twin predicts error 0.5^k -> 0), real loop e0=1, 3000 steps")
print("sigma/d  g/b(pop)  m=bK    regime       real final e  floor d/K   honest-K floor d*b/C")
for r in (0.5, 1.0, 1.5, 2.0, 4.0, 8.0):
    P = p_active(D, r * D)
    K = C / (B * P)
    m = B * K
    tr = loop(B, D, K, steps=3000)
    e = final(tr)
    flo = floor_p(D, K)
    print(f"{r:6.2f}   {P:7.4f}  {m:6.2f}  {regime(m):11s}  {('%.4g' % e) if abs(e) < 1e6 else 'blow-up':>11s}  {flo:8.4f}   {D * B / C:8.4f}")

print("\n== 3. Stability edge m=2 (P = C/2 for the twin-designed K); e0=1; sweep m = b*K")
print("m       regime        final |e|      bound d/K   basin edge b*d/(m-2)")
for m in (0.5, 0.9, 1.1, 1.5, 1.9, 1.99, 2.01, 2.05, 2.2, 2.5):
    tr = loop(B, D, m / B, steps=3000, cap=1e9)
    e = abs(final(tr))
    edge = ('%.3f' % basin_edge(B, D, m)) if m > 2 else '-'
    print(f"{m:5.2f}   {regime(m):12s}  {('%.5f' % e) if e < 1e6 else 'blow-up':>10s}  {D / (m / B):9.5f}   {edge:>8s}")
print("basin check at m=2.5 (edge 0.200): e0=0.19 -> final |e| %.4f ; e0=0.21 -> %s" % (
    abs(loop(B, D, 2.5 / B, e0=0.19, steps=3000, cap=1e9)[-1]),
    "blow-up" if abs(loop(B, D, 2.5 / B, e0=0.21, steps=3000, cap=1e9)[-1]) > 1e6 else "bounded"))

print("\n== 4. Inverse compensation u=-K e - dh*sgn(e), K=C/b, delta=dh-d  (deterministic loop)")
K = C / B
print("delta/d   final |e|   predicted                      cycle")
for dl in (-0.5, -0.25, -0.1, 0.0, 0.1, 0.25, 0.5):
    delta = dl * D
    tr = loop(B, D, K, dh=D + delta, steps=3000)
    e = abs(final(tr))
    pred = abs(delta) / K if delta < 0 else (chatter_amp(B, delta, B * K) if delta > 0 else 0.0)
    cyc = "2-cycle" if delta > 0 and abs(tr[-1] + tr[-2]) < 1e-9 else ("floor" if delta < 0 else "exact")
    print(f"{dl:7.2f}   {e:.6f}   {pred:.6f}  ({'floor |Δ|/K' if delta < 0 else 'bΔ/(2-m)' if delta > 0 else '0'})  {cyc}")
print(f"under- vs over-compensation by the same |Δ|: floor/chatter = {(1 / C) / (1 / (2 - C)):.2f}x at m={C}")

print("\n== 5. Fitting (b, d) instead of one gain: profile least squares, sigma=1.5d, sw=0.02, 300 repeats")
grid = [i * 0.005 for i in range(1, 41)]
print("n      ols g/b   d_hat mean  d_hat RMSE/d  P(d_hat>d)  b_hat RMSE/b  real |e| deadband-comp   uncomp(g_ols)   uncomp(honest K)")
for n in (100, 400, 1600):
    rng = random.Random(100 + n)
    gs, ds, bs, es, eu, e0h = [], [], [], [], [], []
    reps = 300
    for _ in range(reps):
        u, y = simulate_id(n, B, D, 1.5 * D, SW, rng)
        g = ols_gain(u, y)
        b_h, d_h = fit_deadband(u, y, grid)
        gs.append(g / B)
        ds.append(d_h)
        bs.append(b_h)
        Kh = C / b_h
        tr = loop(B, D, Kh, dh=d_h, steps=600, cap=1e6)
        es.append(abs(tr[-1]))
        Kg = C / g
        tg = loop(B, D, Kg, steps=600, cap=1e6)
        eu.append(min(abs(tg[-1]), 1e6))
    tr0 = loop(B, D, C / B, steps=600)
    mean = lambda v: sum(v) / len(v)
    rm = lambda v, t: math.sqrt(mean([(x - t) ** 2 for x in v]))
    print(f"{n:5d}  {mean(gs):7.3f}   {mean(ds):9.4f}   {rm(ds, D) / D:10.3f}   {sum(x > D for x in ds) / reps:9.2f}   {rm(bs, B) / B:10.3f}   "
          f"{mean(es):15.4f}   {mean(eu):13.4f}   {abs(tr0[-1]):13.4f}")
