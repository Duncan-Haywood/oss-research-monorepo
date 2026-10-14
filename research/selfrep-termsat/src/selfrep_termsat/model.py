"""Terminal fleet value ``s`` per machine in the saturating-market reinvestment problem.

Objective: goods revenue ``R(g) = a c (1 - exp(-g/c))`` over [0, T] plus ``s`` times the fleet at T.
Dynamics, Euler step and policy families are those of ``selfrep_satmarket`` (imported by relative
path, not copied). Only the terminal condition of the dynamic programme is new: ``V_T(n) = s n``.
"""
import math
import pathlib
import sys

_root = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_root / "selfrep-satmarket" / "src"))
from selfrep_satmarket.model import Params, bang_bang, dp_policy, revenue, run  # noqa: E402,F401


def value(p, policy, s, n0=1.0):
    """Euler objective: goods revenue plus ``s`` x final fleet."""
    g, n, path = run(p, policy, n0)
    return g + s * n, n, path


def best_switch(p, s, step=1.0):
    best, ts = (0.0, -1.0, 0.0), 0.0
    while ts <= p.horizon + 1e-9:
        j, n, _ = value(p, bang_bang(ts), s)
        if j > best[1]:
            best = (ts, j, n)
        ts += step
    return best


def dp_solve(p, s, n_points=400, u_levels=21, n0=1.0):
    """Backward DP as in ``selfrep_satmarket.dp_solve`` with terminal value ``V_T(n) = s n``.

    Difference: a successor beyond the top of the fleet grid is valued by linear extrapolation in ``n``
    (the satmarket DP holds the edge value flat, which is harmless when the terminal value is 0 but
    undervalues growth when the terminal value is ``s n``).
    """
    steps = int(round(p.horizon / p.dt))
    top = math.log((1 + p.k * p.dt) ** steps)
    h = top / (n_points - 1)
    grid = [n0 * math.exp(i * h) for i in range(n_points)]
    us = [j / (u_levels - 1) for j in range(u_levels)]
    shift = [math.log1p(p.k * u * p.dt) / h for u in us]
    rev = [[revenue(p, (1 - u) * n) * p.dt for u in us] for n in grid]
    v = [s * n for n in grid]
    pol = [None] * steps
    for t in range(steps - 1, -1, -1):
        slope = (v[-1] - v[-2]) / (grid[-1] - grid[-2])    # linear extrapolation past the grid edge
        nv, pl = [0.0] * n_points, [0.0] * n_points
        for i in range(n_points):
            best, bu = -1.0, 0.0
            for j, u in enumerate(us):
                pos = i + shift[j]
                lo = int(pos)
                if lo >= n_points - 1:
                    nxt = v[-1] + slope * grid[-1] * (math.exp((pos - (n_points - 1)) * h) - 1)
                else:
                    f = pos - lo
                    nxt = v[lo] * (1 - f) + v[lo + 1] * f
                val = rev[i][j] + nxt
                if val > best:
                    best, bu = val, u
            nv[i], pl[i] = best, bu
        v, pol[t] = nv, pl
    return v[0], pol, grid
