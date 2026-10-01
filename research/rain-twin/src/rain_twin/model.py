"""Radar detection range under rain attenuation, stylised.

Real system: monostatic radar, free-space clear-air detection range r0. One-way rain attenuation is gamma = k R^alpha dB/km for rain rate
R (mm/h); in nepers (power) per km kappa = (ln 10 / 10) gamma. Two-way power factor exp(-2 kappa r), so the target is detected iff
4 ln(r0/r) >= 2 kappa r, i.e. r <= r_d(kappa) = (2/kappa) W(kappa r0 / 2) with W the Lambert function.
Rain is intermittent: R = 0 with probability 1-p, otherwise exponential with mean m.
"""
import math
import random

LN10_10 = math.log(10.0) / 10.0


def lambertw(x, tol=1e-14):
    """Principal branch for x >= 0 by Halley iteration."""
    if x == 0:
        return 0.0
    w = math.log1p(x) if x < 3 else math.log(x) - math.log(math.log(x))
    for _ in range(100):
        e = math.exp(w)
        f = w * e - x
        step = f / (e * (w + 1) - (w + 2) * f / (2 * w + 2))
        w -= step
        if abs(step) < tol * (1 + abs(w)):
            break
    return w


def kappa(R, k, alpha):
    """Power attenuation in nepers/km for rain rate R (mm/h)."""
    return LN10_10 * k * R ** alpha if R > 0 else 0.0


def rain_rate(kap, k, alpha):
    """Inverse of kappa."""
    return (kap / (LN10_10 * k)) ** (1.0 / alpha) if kap > 0 else 0.0


def detect(r, kap, r0):
    """True iff the target at range r (km) is detected under attenuation kap (nepers/km)."""
    return 4 * math.log(r0 / r) >= 2 * kap * r if r <= r0 else False


def r_d(kap, r0):
    """Detection range: root of r = r0 exp(-kap r / 2), r = (2/kap) W(kap r0/2). kap = 0 gives r0."""
    if kap <= 0:
        return r0
    return (2.0 / kap) * lambertw(kap * r0 / 2.0)


def kappa_star(r, r0):
    """Largest attenuation at which range r is still detected: 2 ln(r0/r)/r (0 for r >= r0)."""
    return 2.0 * math.log(r0 / r) / r if r < r0 else 0.0


def p_detect(r, r0, k, alpha, p, m):
    """Real detection probability at range r: P(R <= R*(r)) with R = 0 w.p. 1-p and Exp(mean m) otherwise."""
    if r >= r0:
        return 0.0 if r > r0 else 1.0 - p
    Rs = rain_rate(kappa_star(r, r0), k, alpha)
    return 1.0 - p * math.exp(-Rs / m)


def quantile_range(q, r0, k, alpha, p, m):
    """Range whose detection probability equals q (q in (0,1)); detection probability is decreasing in r. Bisection on (0, r0]."""
    lo, hi = 1e-9, r0
    if p_detect(hi, r0, k, alpha, p, m) >= q:
        return r0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if p_detect(mid, r0, k, alpha, p, m) >= q:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def mean_range(r0, k, alpha, p, m, n=200000):
    """E[r_d] = (1-p) r0 + p E[r_d(kappa(R)) | rain], midpoint rule on the exponential quantile u in (0,1) (R = -m ln(1-u))."""
    s = 0.0
    for i in range(n):
        u = (i + 0.5) / n
        s += r_d(kappa(-m * math.log(1 - u), k, alpha), r0)
    return (1 - p) * r0 + p * s / n


def mean_rain(p, m):
    return p * m


def sample_rain(rng, p, m):
    return rng.expovariate(1.0 / m) if rng.random() < p else 0.0


def brier_deterministic(rs, r0, k, alpha, p, m, r_twin):
    """Brier of a deterministic twin that predicts detection iff r <= r_twin: mean over ranges of (1[r<=r_twin] - P_real)^2 + P(1-P)."""
    s = 0.0
    for r in rs:
        P = p_detect(r, r0, k, alpha, p, m)
        y = 1.0 if r <= r_twin else 0.0
        s += (y - P) ** 2 + P * (1 - P)
    return s / len(rs)


def brier_calibrated(rs, r0, k, alpha, p, m, p_t, m_t):
    """Brier (expected, against real outcomes) of a twin reporting its own rain climatology (p_t, m_t) as a probability."""
    s = 0.0
    for r in rs:
        P = p_detect(r, r0, k, alpha, p, m)
        Q = p_detect(r, r0, k, alpha, p_t, m_t)
        s += (Q - P) ** 2 + P * (1 - P)
    return s / len(rs)
