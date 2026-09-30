"""Deadband twin.  Real actuator: applied = D(u) = u - d*sign(u) for |u|>d, else 0.  Plant x' = x + b*D(u).
The twin is linear: x' = x + g*u.  g is fitted by OLS (through the origin) from Gaussian-dither logs
y = b*D(u) + w.  Bussgang/Stein: E[u D(u)] = s2 * P(|u|>d), so plim g = b * P(|u|>d).

Regulation to r=0 with u = -K e, e = x.  For |K e|>d the real error obeys e' = (1-m) e + b d sgn(e), m = bK,
with fixed point d/K.  m<1: monotone approach to d/K from outside (never enters the dead zone);
1<m<2: alternates, |e'| = (m-1)|e| - b d, and stops inside the zone; m>2: the same map has a repelling
magnitude b d/(m-2): |e0| below it stops inside the zone, above it diverges (basin, not global instability).
Inverse compensation u = -K e - dh*sgn(e), D = dh - d error Delta = dh - d:
Delta<0 leaves the floor |Delta|/K; Delta>0 chatters in a 2-cycle of amplitude b*Delta/(2-m).
"""
import math
import random


def deadband(u, d):
    if u > d:
        return u - d
    if u < -d:
        return u + d
    return 0.0


def p_active(d, sigma):
    """P(|u|>d) for u ~ N(0, sigma^2)."""
    return math.erfc(d / (sigma * math.sqrt(2.0)))


def plim_ols(b, d, sigma):
    return b * p_active(d, sigma)


def simulate_id(n, b, d, sigma, sw, rng):
    u = [rng.gauss(0, sigma) for _ in range(n)]
    y = [b * deadband(t, d) + rng.gauss(0, sw) for t in u]
    return u, y


def ols_gain(u, y):
    return sum(s * t for s, t in zip(u, y)) / sum(s * s for s in u)


def fit_deadband(u, y, d_grid):
    """Profile least squares: for each d the best b is closed-form; pick the d with least SSE."""
    best = None
    for d in d_grid:
        z = [deadband(t, d) for t in u]
        zz = sum(v * v for v in z)
        if zz == 0.0:
            continue
        b = sum(v * t for v, t in zip(z, y)) / zz
        sse = sum((t - b * v) ** 2 for v, t in zip(z, y))
        if best is None or sse < best[0]:
            best = (sse, b, d)
    return best[1], best[2]


def loop(b, d, K, e0=1.0, steps=2000, dh=0.0, cap=1e12):
    """Real loop with u = -K e - dh sgn(e).  Returns the error trajectory (stops if it blows up)."""
    e, out = e0, [e0]
    for _ in range(steps):
        s = 1.0 if e > 0 else (-1.0 if e < 0 else 0.0)
        e = e + b * deadband(-K * e - dh * s, d)
        out.append(e)
        if abs(e) > cap:
            break
    return out


def floor_p(d, K):
    return d / K


def chatter_amp(b, delta, m):
    return b * delta / (2.0 - m)


def basin_edge(b, d, m):
    """For m>2: |e0| above this diverges, below it the loop stops inside the dead zone."""
    return b * d / (m - 2.0)
