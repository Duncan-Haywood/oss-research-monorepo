"""Windup twin.  Real plant: integrator x' = u with a saturating actuator, under PI control
u = -sat_U(v),  v = kp x + ki z,  z' = x,  start x(0) = x0 > 0, z(0) = 0.  Twin: no saturation.
With ki = wn^2, kp = 2 zeta wn the linear loop is z'' + kp z' + ki z = 0 with x = z'.  Because z(0) = 0 the
twin's x starts at x0 with x'(0) = -kp x0, and (for zeta >= 1) it still undershoots the target by a fixed fraction of x0.
Real, a = kp x0 / U > 1: saturated phase x = x0 - U t, z = x0 t - U t^2/2 until v = U again at t1 (larger root of a
quadratic), then the same linear loop from (x1, x'= -U).  Conditional integration (freeze z while |v| > U) re-enters
the linear regime from x = U/kp with z = 0, i.e. it replays the twin's own trajectory from x0' = U/kp.
"""
import math


def gains(wn, zeta):
    return 2.0 * zeta * wn, wn * wn          # kp, ki


def _lin_extremum(x, xd, kp, ki):
    """First extremum (x' = 0) of x'' + kp x' + ki x = 0 from (x, x') at tau = 0, strictly after tau = 0 when x' != 0.
    Returns (tau, x(tau))."""
    disc = kp * kp - 4.0 * ki
    if abs(disc) < 1e-12 * kp * kp:                      # critical: x = (A + B tau) e^{-w tau}
        w = kp / 2.0
        A, B = x, xd + w * x
        if abs(B) < 1e-300:
            return float("inf"), 0.0
        tau = (B - w * A) / (w * B)
        return tau, (A + B * tau) * math.exp(-w * tau)
    if disc > 0:                                         # overdamped
        s = math.sqrt(disc)
        r1, r2 = (-kp + s) / 2.0, (-kp - s) / 2.0
        A = (xd - r2 * x) / (r1 - r2)
        B = x - A
        q = -B * r2 / (A * r1) if A * r1 != 0 else -1.0
        if q <= 0:
            return float("inf"), 0.0
        tau = math.log(q) / (r1 - r2)
        if tau <= 0:
            return float("inf"), 0.0
        return tau, A * math.exp(r1 * tau) + B * math.exp(r2 * tau)
    sg, wd = kp / 2.0, math.sqrt(-disc) / 2.0            # underdamped: x = e^{-sg tau}(C cos + D sin)
    C = x
    D = (xd + sg * x) / wd
    a = -sg * C + wd * D
    b = -sg * D - wd * C
    tau = math.atan2(a, -b) / wd                         # a cos + b sin = 0  ->  tan = -a/b
    while tau <= 1e-14:
        tau += math.pi / wd
    return tau, math.exp(-sg * tau) * (C * math.cos(wd * tau) + D * math.sin(wd * tau))


def twin_overshoot(wn, zeta):
    """Twin's undershoot past the target as a fraction of x0 (independent of x0 by linearity)."""
    kp, ki = gains(wn, zeta)
    _, xm = _lin_extremum(1.0, -kp, kp, ki)
    return max(0.0, -xm)


def exit_time(x0, U, kp, ki):
    """Time the saturated phase ends (v returns to U); None if a <= 1 (never saturated)."""
    if kp * x0 <= U:
        return None
    # v(t) = kp x0 + (ki x0 - kp U) t - (ki U / 2) t^2 = U  -> (ki U/2) t^2 - (ki x0 - kp U) t - (kp x0 - U) = 0
    A, B, C = ki * U / 2.0, -(ki * x0 - kp * U), -(kp * x0 - U)
    return (-B + math.sqrt(B * B - 4 * A * C)) / (2 * A)


def real_overshoot(x0, U, wn, zeta):
    """Exact real undershoot |min x| as a fraction of x0, assuming the loop stays unsaturated after the first exit
    (checked against simulation in the tests/experiments)."""
    kp, ki = gains(wn, zeta)
    t1 = exit_time(x0, U, kp, ki)
    if t1 is None:
        return twin_overshoot(wn, zeta)
    x1 = x0 - U * t1
    _, xm = _lin_extremum(x1, -U, kp, ki)
    return max(0.0, -xm / x0)


def clamped_overshoot(x0, U, wn, zeta):
    """Conditional integration: undershoot as a fraction of x0 = twin overshoot replayed from x = U/kp."""
    kp, ki = gains(wn, zeta)
    if kp * x0 <= U:
        return twin_overshoot(wn, zeta)
    return twin_overshoot(wn, zeta) * (U / kp) / x0


def simulate(x0, U, wn, zeta, T, dt=1e-3, mode="none"):
    """RK4 simulation at fine dt (the saturation switch is non-smooth, so agreement is to about dt).
    mode: 'none' (windup), 'clamp' (conditional integration), 'twin' (no saturation).  Returns the list of x at t = dt, 2dt, ..."""
    kp, ki = gains(wn, zeta)

    def f(x, z):
        v = kp * x + ki * z
        if mode == "twin":
            return -v, x
        u = -max(-U, min(U, v))
        dz = x
        if mode == "clamp" and abs(v) > U and v * x > 0:
            dz = 0.0
        return u, dz

    x, z = x0, 0.0
    xs = []
    n = int(round(T / dt))
    for _ in range(n):
        a = f(x, z)
        b = f(x + dt / 2 * a[0], z + dt / 2 * a[1])
        c = f(x + dt / 2 * b[0], z + dt / 2 * b[1])
        d = f(x + dt * c[0], z + dt * c[1])
        x += dt / 6 * (a[0] + 2 * b[0] + 2 * c[0] + d[0])
        z += dt / 6 * (a[1] + 2 * b[1] + 2 * c[1] + d[1])
        xs.append(x)
    return xs


def overshoot_of(xs, x0):
    return max(0.0, -min(xs) / x0)
