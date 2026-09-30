import math
from delayed_outer import *

def grid(kap, n=200):
    return [kap ** (i / (n - 1)) / kap for i in range(n)]

print("E1 stability limit of the stale outer step: a = alpha*s < 2 sin(pi/(4 tau+2)); radius just inside/outside")
for t in (0, 1, 2, 3, 4, 8, 16, 32):
    lim = stable_limit(t)
    print(f" tau={t:2d} limit {lim:.4f}  radius(0.999 lim) {radius(.999*lim, t):.6f}  radius(1.001 lim) {radius(1.001*lim, t):.6f}  pi/(2 tau+1) {math.pi/(2*t+1):.4f}")

print("\nE2 fastest single mode: a* = tau^tau/(tau+1)^(tau+1), radius tau/(tau+1)")
for t in (1, 2, 3, 5, 10):
    a, r = single_optimal(t)
    print(f" tau={t:2d} a* {a:.5f} radius {r:.4f} (numeric {radius(a, t):.4f})  rounds to 1e-6: {rounds(r, 1e-6):6.1f}")

print("\nE3 what a delay costs: in-flight rounds gained (tau+1) x step cap paid; rounds x period vs blocking")
print(" kappa=1000, eta=1/a_max, H=16, tuned alpha, sync-dominated (C >> H so period = (H+C)/(tau+1))")
print(" tau  (tau+1)*limit  tuned alpha  rate     rounds-to-1e-6  time/blocking")
H = 16
lo = curvature(1, 1e-3, H)
base = rounds(best_alpha(lo, 1.0, 0)[1], 1e-6)
for t in (0, 1, 2, 3, 4, 6, 8, 16):
    al, r = best_alpha(lo, 1.0, t)
    print(f" {t:3d}  {delay_price(t):10.3f}  {al:10.3f}  {r:.5f}  {rounds(r,1e-6):10.0f}  {rounds(r,1e-6)/(t+1)/base:12.3f}")

print("\nE4 best design (H, tau) vs blocking, kappa=1000, eps=1e-6, H capped by drift/bias budget Hmax")
print(" Hmax    C | blocking H  time | naive best (H,tau) time  gain | compensated lam=1 (H,tau) time  gain")
T = [0, 1, 2, 3, 4, 6, 8, 12, 16]
for Hmax in (16, 64):
    Hs = [h for h in (1, 4, 16, 64) if h <= Hmax]
    for C in (64, 1024):
        a = best_design(1000, C, 1e-6, Hs, [0])
        b = best_design(1000, C, 1e-6, Hs, T)
        c = best_design(1000, C, 1e-6, Hs, T, lam=1.0)
        print(f" {Hmax:4d} {C:5d} | {a[0]:6d} {a[2]:10.0f} | ({b[0]:3d},{b[1]:2d}) {b[2]:10.0f} x{a[2]/b[2]:5.2f} | ({c[0]:3d},{c[1]:2d}) {c[2]:10.0f} x{a[2]/c[2]:6.1f}")

print("\nE5 plain averaging (alpha=1) with s_max=1 under delay: radius and literal blow-up")
for t in (0, 1, 2, 3, 6):
    tr = simulate([1.0], 1.0, 1, 1.0, t, 300)
    print(f" tau={t}  radius {radius(1.0, t):.4f}  |x| after 300 rounds {tr[-1]:.3g}")

print("\nE6 delay compensation with curvature estimate off by factor lam (kappa=1000, H=16, tau=4): tuned alpha, rate, stability cap")
print(" lam   cap on alpha*s   tuned alpha  rate     rounds-to-1e-6  vs delay-free")
free = best_alpha(lo, 1.0, 0)[1]
for lam in (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0):
    al, r = best_alpha(lo, 1.0, 4, lam=lam)
    print(f" {lam:4.2f}  {stable_a(4, lam):10.3f}  {al:12.3f}  {r:.5f}  {rounds(r,1e-6):10.0f}  x{rounds(r,1e-6)/rounds(free,1e-6):6.1f}")

print("\nE7 literal simulation vs exact rate (kappa=200 log-grid of 12 modes, window 300)")
a12 = grid(200, 12)
for H, t, lam in ((1, 2, 0.0), (7, 3, 0.0), (40, 1, 0.0), (7, 4, 1.0), (7, 4, 0.6)):
    ss = [curvature(1.0, a, H) for a in a12]
    al, r = best_alpha(min(ss), max(ss), t, lam=lam)
    n = min(6000, int(120 / -math.log(max(r, 1e-9))) + 600)
    tr = simulate(a12, 1.0, H, al, t, n, lam=lam)
    print(f" H={H:3d} tau={t} lam={lam:.1f} alpha={al:.3f} exact {r:.4f} simulated {measured_rate(tr, min(300, n//4)):.4f}")
