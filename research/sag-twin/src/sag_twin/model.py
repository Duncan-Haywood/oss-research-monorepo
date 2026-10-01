"""Battery sag: ideal-source (energy bucket) twin vs a Thevenin pack under constant power, stylised.

Pack: open-circuit voltage falls linearly with charge drawn x (Ah): v(x) = V0 - m x, series resistance R (ohm), capacity C (Ah).
Load: constant power P (W). Terminal voltage vt = v - I R with I vt = P, so I = (v - sqrt(v^2 - 4RP)) / (2R) = 2P / (v + sqrt(v^2 - 4RP)).
The flight ends when vt hits the cutoff Vc (equivalently v = Vc + RP/Vc) or the charge is exhausted (x = C).
Since dt = dx / I and dv = -m dx, the real runtime (hours) has the closed form
    t = 1/(2 P m) * int_{v_end}^{V0} (v + sqrt(v^2 - a^2)) dv,  a^2 = 4 R P.
The twin has R = 0: all stored energy int v dx = (V0^2 - v_end^2)/(2m) reaches the load, t = E / P.
"""
import math


def v_end(P, R, V0, m, C, Vc):
    """Open-circuit voltage at which the real flight ends (None if the pack cannot start: v_end >= V0)."""
    v = max(V0 - m * C, Vc + R * P / Vc)
    return v if v < V0 else None


def _prim(v, a2):
    """Antiderivative of v + sqrt(v^2 - a2)."""
    if a2 <= 0:
        return v * v
    s = math.sqrt(max(v * v - a2, 0.0))
    return v * v / 2 + v * s / 2 - a2 / 2 * math.log(v + s)


def runtime_real(P, R, V0, m, C, Vc):
    ve = v_end(P, R, V0, m, C, Vc)
    if ve is None:
        return 0.0
    a2 = 4 * R * P
    return (_prim(V0, a2) - _prim(ve, a2)) / (2 * P * m)


def runtime_twin(P, V0, m, C, Vc):
    """Ideal source: energy bucket over the same open-circuit curve and the same cutoff (R = 0)."""
    ve = max(V0 - m * C, Vc)
    return (V0 * V0 - ve * ve) / (2 * m * P)


def runtime_numeric(P, R, V0, m, C, Vc, n=200000):
    """Midpoint integration of dt = dx / I(x) up to the cutoff; independent of the closed form."""
    t, h = 0.0, C / n
    for i in range(n):
        v = V0 - m * (i + 0.5) * h
        d = v * v - 4 * R * P
        if d < 0:
            break
        i_a = (v - math.sqrt(d)) / (2 * R) if R > 0 else P / v
        if v - i_a * R < Vc:
            # partial last step: stop at the cutoff
            break
        t += h / i_a
    return t


def efficiency(P, R, V0, m, C, Vc):
    """Real runtime over twin runtime: the fraction of the twin's energy claim that is actually delivered."""
    return runtime_real(P, R, V0, m, C, Vc) / runtime_twin(P, V0, m, C, Vc)


def p_start(R, V0, Vc):
    """Largest power with a non-empty flight: cutoff already reached at full charge when Vc + R P / Vc = V0."""
    return Vc * (V0 - Vc) / R


def hover_power(mass, P0, m0):
    """Momentum-theory scaling: hover power grows as mass^(3/2)."""
    return P0 * (mass / m0) ** 1.5


def max_payload(tau, P0, m0, runtime, hi=50.0):
    """Largest payload (same units as m0) with runtime(P) >= tau; runtime is decreasing in P. Bisection."""
    lo = 0.0
    if runtime(hover_power(m0, P0, m0)) < tau:
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if runtime(hover_power(m0 + mid, P0, m0)) >= tau:
            lo = mid
        else:
            hi = mid
    return lo
