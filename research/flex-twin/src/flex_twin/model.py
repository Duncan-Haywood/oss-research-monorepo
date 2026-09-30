"""Flex twin.  Real plant: motor inertia Jm and load inertia Jl joined by a spring k and damper b (flexible joint).
Twin: rigid body of inertia J = Jm + Jl.  Controller: PD torque on the motor, u = -(kp*q + kd*q').

Units: J = 1 and resonance frequency wr = sqrt(k/mu) = 1 with mu = Jm*Jl/J, so r = Jl/Jm and the structural
damping ratio zs (of the relative mode, b = 2 zs mu) are the only plant parameters.

Non-collocated (q = load position): char. poly  Jm Jl s^4 + J b s^3 + J k s^2 + b kd s^2 + (b kp + k kd) s + k kp.
Collocated (q = motor position):    (Jm s^2)(Jl s^2 + c) + Jl s^2 c + (kd s + kp)(Jl s^2 + c), c = k + b s.
Twin:  J s^2 + kd s + kp, stable for every kp, kd > 0.
"""
import cmath
import math


def plant(r, zs):
    J = 1.0
    Jl = r / (1 + r)
    Jm = 1 / (1 + r)
    mu = Jm * Jl / J
    return Jm, Jl, mu, 2 * zs * mu  # k = mu (wr = 1), b


def polymul(a, b):
    out = [0.0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
    return out


def polyadd(a, b):
    n = max(len(a), len(b))
    a = [0.0] * (n - len(a)) + list(a)
    b = [0.0] * (n - len(b)) + list(b)
    return [x + y for x, y in zip(a, b)]


def char_poly(r, zs, kp, kd, collocated=False):
    """Coefficients, highest power first.  Motor: Jm s^2 qm = u - c (qm-ql); load: Jl s^2 ql = c (qm-ql), c = k + b s."""
    Jm, Jl, mu, b = plant(r, zs)
    k = mu
    c = [b, k]
    # ql = c/(Jl s^2 + c) qm ; motor: (Jm s^2 + Jl s^2 c/(Jl s^2 + c)) qm = -(kd s + kp) q
    den = [Jl, 0.0, 0.0]
    den = polyadd(den, c)                           # Jl s^2 + c
    lhs = polyadd(polymul([Jm, 0, 0], den), polymul([Jl, 0, 0], c))   # (Jm s^2)(Jl s^2 + c) + Jl s^2 c
    ctrl = [kd, kp]
    if collocated:  # q = qm
        return polyadd(lhs, polymul(ctrl, den))
    return polyadd(lhs, polymul(ctrl, c))           # q = ql = c/den * qm


def roots(p, iters=2000):
    """Durand-Kerner for a real polynomial, highest power first."""
    n = len(p) - 1
    p = [x / p[0] for x in p]
    z = [(0.4 + 0.9j) ** i for i in range(n)]
    for _ in range(iters):
        new = []
        for i in range(n):
            v = sum(p[j] * z[i] ** (n - j) for j in range(n + 1))
            d = 1.0
            for j in range(n):
                if j != i:
                    d *= z[i] - z[j]
            new.append(z[i] - v / d)
        done = max(abs(a - b) for a, b in zip(new, z)) < 1e-14
        z = new
        if done:
            break
    return z


def abscissa(p):
    return max(z.real for z in roots(p))


def routh_stable(r, zs, kp, kd):
    """Hurwitz conditions for the non-collocated quartic a4..a0."""
    a4, a3, a2, a1, a0 = char_poly(r, zs, kp, kd)
    return min(a4, a3, a2, a1, a0) > 0 and a3 * a2 > a4 * a1 and a1 * (a3 * a2 - a4 * a1) > a3 ** 2 * a0


def design(wn, zeta=0.7):
    """Twin design for J = 1: kp = wn^2, kd = 2 zeta wn."""
    return wn * wn, 2 * zeta * wn


def max_stable_wn(r, zs, zeta=0.7, collocated=False, hi=50.0):
    """Largest design bandwidth wn below which the real loop is stable (bisect on the first crossing from a
    stable low-gain start; the stable set is an interval in wn for the cases tried)."""
    lo = 1e-3
    def st(w):
        kp, kd = design(w, zeta)
        return abscissa(char_poly(r, zs, kp, kd, collocated)) < 0
    if not st(lo):
        return 0.0
    # scan upwards to bracket the first instability
    w = lo
    while w < hi and st(w):
        w *= 1.05
    if w >= hi:
        return float("inf")
    a, b = w / 1.05, w
    for _ in range(60):
        m = (a + b) / 2
        if st(m):
            a = m
        else:
            b = m
    return a


def simulate(r, zs, kp, kd, T, dt=0.005, x0=1.0, collocated=False, twin=False):
    """RK4 step response from load = motor = x0 at rest (regulation to 0).  Returns list of load (or rigid) positions."""
    Jm, Jl, mu, b = plant(r, zs)
    k = mu
    def f(s):
        qm, wm, ql, wl = s
        q, w = (qm, wm) if collocated else (ql, wl)
        if twin:
            return (wm, -(kp * q + kd * w) / 1.0, wm, -(kp * q + kd * w) / 1.0)
        u = -(kp * q + kd * w)
        t = k * (qm - ql) + b * (wm - wl)
        return (wm, (u - t) / Jm, wl, t / Jl)
    s = (x0, 0.0, x0, 0.0)
    out = []
    for _ in range(int(T / dt)):
        k1 = f(s)
        k2 = f(tuple(a + dt / 2 * c for a, c in zip(s, k1)))
        k3 = f(tuple(a + dt / 2 * c for a, c in zip(s, k2)))
        k4 = f(tuple(a + dt * c for a, c in zip(s, k3)))
        s = tuple(a + dt / 6 * (c1 + 2 * c2 + 2 * c3 + c4) for a, c1, c2, c3, c4 in zip(s, k1, k2, k3, k4))
        out.append(s[2])
    return out


def boundary_cubic(wn, zs, zeta=0.7):
    """Both Hurwitz conditions reduce to inequalities free of the mass ratio r (mu cancels).  The binding one,
    a1 (a3 a2 - a4 a1) > a3^2 a0, becomes  g(wn) = zs^2 wn^3 + zs (q + zeta) wn^2 + zeta q wn - zeta zs < 0
    with q = zeta (1 - 4 zs^2).  For zs < 1/2 every coefficient but the last is positive, so g is increasing and the
    stable set is exactly wn < wn_star, the unique positive root."""
    q = zeta * (1 - 4 * zs * zs)
    return zs * zs * wn ** 3 + zs * (q + zeta) * wn ** 2 + zeta * q * wn - zeta * zs


def wn_star(zs, zeta=0.7):
    """Design bandwidth (in units of the resonance) at which the non-collocated PD loop first loses stability."""
    assert 0 < zs < 0.5
    a, b = 0.0, 1.0
    while boundary_cubic(b, zs, zeta) < 0:
        b *= 2
    for _ in range(200):
        m = (a + b) / 2
        if boundary_cubic(m, zs, zeta) < 0:
            a = m
        else:
            b = m
    return (a + b) / 2


def zs_required(wn, zeta=0.7):
    """Smallest structural damping ratio for which design bandwidth wn (resonance = 1) is stable (g decreasing in zs
    on the range used here; checked against the characteristic roots in the tests)."""
    a, b = 1e-9, 0.4999
    for _ in range(200):
        m = (a + b) / 2
        if boundary_cubic(wn, m, zeta) < 0:
            b = m
        else:
            a = m
    return (a + b) / 2
