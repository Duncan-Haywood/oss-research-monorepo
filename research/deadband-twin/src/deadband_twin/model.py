"""Deadband twin.  Real actuator: y = g*D(u) + w, D(u) = u - delta*sign(u) for |u| > delta, else 0.
The twin is linear, y = b*u, fitted by OLS on logged (u, y) with u ~ N(0, s2).

Exact Gaussian facts (d = delta/s):  cov(u, D(u)) = s2 * 2Q(d), with Q the standard normal tail, so plim OLS = g*2Q(d) = g*P(|z| > d),
the probability that the excitation leaves the deadband.  Var D(u) = s2 * (2Q(d)(1+d^2) - 2 d phi(d)).
For a sinusoid of amplitude A > delta the describing-function gain is 1 - (2/pi)(asin r + r sqrt(1-r^2)), r = delta/A.
"""
import math
import random


def dead(u, delta):
    if u > delta:
        return u - delta
    if u < -delta:
        return u + delta
    return 0.0


def q2(d):
    """2Q(d) = P(|z| > d)."""
    return math.erfc(d / math.sqrt(2.0))


def phi(d):
    return math.exp(-d * d / 2.0) / math.sqrt(2.0 * math.pi)


def plim_gain(g, delta, s):
    return g * q2(delta / s)


def var_dead(delta, s):
    d = delta / s
    return s * s * (q2(d) * (1.0 + d * d) - 2.0 * d * phi(d))


def sine_gain(delta, amp):
    if amp <= delta:
        return 0.0
    r = delta / amp
    return 1.0 - (2.0 / math.pi) * (math.asin(r) + r * math.sqrt(1.0 - r * r))


def simulate(n, g, delta, s, sw, rng):
    u = [rng.gauss(0.0, s) for _ in range(n)]
    y = [g * dead(t, delta) + rng.gauss(0.0, sw) for t in u]
    return u, y


def _mean(v):
    return sum(v) / len(v)


def cov(p, q):
    mp, mq = _mean(p), _mean(q)
    return sum((a - mp) * (b - mq) for a, b in zip(p, q)) / (len(p) - 1)


def ols(u, y):
    return cov(u, y) / cov(u, u)


def r2_line(u, y, b):
    my, mu = _mean(y), _mean(u)
    res = sum(((t - my) - b * (s - mu)) ** 2 for s, t in zip(u, y))
    tot = sum((t - my) ** 2 for t in y)
    return 1.0 - res / tot


def fit_deadband(u, y, grid=None):
    """Fit (g, delta): for each delta on a grid regress y on D(u); refine around the best grid point."""
    su = math.sqrt(cov(u, u))

    def sse(delta):
        z = [dead(t, delta) for t in u]
        v = cov(z, z)
        if v <= 0.0:
            return float("inf"), 0.0
        gh = cov(z, y) / v
        my, mz = _mean(y), _mean(z)
        return sum(((t - my) - gh * (s - mz)) ** 2 for s, t in zip(z, y)), gh

    if grid is None:
        grid = [su * 0.05 * k for k in range(0, 41)]
    best = min(grid, key=lambda dl: sse(dl)[0])
    lo, hi = max(0.0, best - su * 0.05), best + su * 0.05
    for _ in range(30):  # golden-free ternary refinement (SSE is unimodal locally)
        m1, m2 = lo + (hi - lo) / 3.0, hi - (hi - lo) / 3.0
        if sse(m1)[0] < sse(m2)[0]:
            hi = m2
        else:
            lo = m1
    dl = 0.5 * (lo + hi)
    return sse(dl)[1], dl


def stall_error(e0, k, delta, steps=500):
    """Error e = r - x of the loop x <- x + D(k e) (twin: linear, converges to 0 for 0 < k < 2)."""
    e = e0
    for _ in range(steps):
        e = e - dead(k * e, delta)
    return e
