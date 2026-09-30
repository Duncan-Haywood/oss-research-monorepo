"""Drag twin.  Real vehicle (unit mass): v' = F - k v^2 (quadratic drag, v >= 0).  Twin: v' = F - c v (linear drag) with c fitted
from coast-down (F = 0) data.  Everything real is closed form:
coast-down v(t) = v0/(1 + k v0 t), distance ln(1 + k v0 t)/k (no stopping point), terminal speed sqrt(F/k),
step response v(t) = v* (vs + v* tanh(k v* t))/(v* + vs tanh(k v* t)).  Twin: v0 e^{-ct}, distance (v0 - vf)/c, terminal F/c.
"""
import math
import random


def real_coast_speed(t, v0, k):
    return v0 / (1 + k * v0 * t)


def real_time_to(vf, v0, k):
    return (1 / vf - 1 / v0) / k


def real_dist_to(vf, v0, k):
    return math.log(v0 / vf) / k


def twin_time_to(vf, v0, c):
    return math.log(v0 / vf) / c


def twin_dist_to(vf, v0, c):
    return (v0 - vf) / c


def secant_c(k, vcal):
    """Linear drag matching the real drag force at vcal: c v = k v^2."""
    return k * vcal


def tangent_c(k, vcal):
    """Linear drag matching the real drag slope at vcal: c = d(k v^2)/dv."""
    return 2 * k * vcal


def ls_force_fit_c(k, vmax, vmin=0.0):
    """Least squares through the origin of decel (= k v^2) on v, v uniform on [vmin, vmax]: c = k E[v^3]/E[v^2]."""
    m3 = (vmax ** 4 - vmin ** 4) / 4
    m2 = (vmax ** 3 - vmin ** 3) / 3
    return k * m3 / m2


def terminal_real(F, k):
    return math.sqrt(F / k)


def terminal_twin(F, c):
    return F / c


def energy_per_dist_real(v, k):
    """Drag work per unit distance at steady speed v."""
    return k * v * v


def energy_per_dist_twin(v, c):
    return c * v


def real_step_speed(t, vs, F, k):
    vst = math.sqrt(F / k)
    th = math.tanh(k * vst * t)
    return vst * (vs + vst * th) / (vst + vs * th)


def twin_step_speed(t, vs, F, c):
    vt = F / c
    return vt + (vs - vt) * math.exp(-c * t)


def time_to_fraction(speed_fn, vs, vend, frac=1 - math.exp(-1)):
    """First time the (monotone) step response has covered `frac` of the step vs -> vend."""
    target = vs + frac * (vend - vs)
    lo, hi = 0.0, 1.0
    up = vend > vs
    while (speed_fn(hi) < target) if up else (speed_fn(hi) > target):
        hi *= 2
        if hi > 1e9:
            return float("inf")
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if (speed_fn(mid) < target) if up else (speed_fn(mid) > target):
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def coast_data(v0, k, dt, T, noise, rng):
    """Noisy speed samples of a real coast-down (exact solution plus N(0, noise^2))."""
    n = int(round(T / dt))
    return [(i * dt, real_coast_speed(i * dt, v0, k) + rng.gauss(0, noise)) for i in range(n + 1)]


def fit_c_from_speed(data):
    """Least-squares c of v = v0 e^{-ct} on the log of positive samples, v0 free: slope of ln v on t."""
    pts = [(t, math.log(v)) for t, v in data if v > 0]
    n = len(pts)
    mt = sum(p[0] for p in pts) / n
    ml = sum(p[1] for p in pts) / n
    return -sum((t - mt) * (l - ml) for t, l in pts) / sum((t - mt) ** 2 for t, _ in pts)


def fit_c_from_accel(data, dt):
    """Through-origin regression of finite-difference deceleration on mid-point speed."""
    num = den = 0.0
    for (t0, v0), (t1, v1) in zip(data, data[1:]):
        a, v = (v0 - v1) / dt, 0.5 * (v0 + v1)
        num += a * v
        den += v * v
    return num / den
