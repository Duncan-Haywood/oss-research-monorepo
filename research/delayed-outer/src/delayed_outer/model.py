"""Overlapped ("streaming") outer synchronisation in DiLoCo-style training, on a quadratic (companion to
outer-momentum, which assumed the outer step is applied the moment the round ends).
Loss (1/2) sum_i a_i x_i^2. A round of H inner steps of size eta from the global point x_t yields the pseudo-gradient
g_t = s x_t with s = 1 - (1 - eta a)^H in (0, 1]. To hide a synchronisation of latency C behind compute, the outer
step uses a gradient that is tau rounds old:
    x_{t+1} = x_t - alpha g_{t-tau} = x_t - a x_{t-tau},   a = alpha s.
Characteristic polynomial z^(tau+1) - z^tau + a. Exact facts used here:
  * stable iff a < 2 sin(pi / (4 tau + 2))                      (tau = 0: a < 2; tau = 1: a < 1; ~ pi/(2 tau))
  * fastest single mode: a* = tau^tau / (tau+1)^(tau+1), radius tau/(tau+1)  (double root at z = tau/(tau+1))
Delay compensation: the server also knows the updates applied since g_{t-tau} was computed and a per-coordinate
curvature estimate (a secant of past pseudo-gradients recovers s exactly on a quadratic), so it extrapolates
    x_{t+1} = x_t - alpha (g_{t-tau} + lam s (x_t - x_{t-tau})),   lam = ratio of estimated to true curvature,
with characteristic polynomial z^(tau+1) - (1 - lam a) z^tau + (1 - lam) a; lam = 0 is the naive stale update and
lam = 1 removes the delay exactly (roots 1 - a and 0).
A round takes max(H, (H + C)/(tau + 1)) time: tau + 1 rounds in flight share one round-trip of H + C."""
import cmath
import math

__all__ = ["curvature", "stable_limit", "radius", "single_optimal", "rate", "best_alpha", "rounds", "period",
           "wallclock", "best_design", "simulate", "measured_rate", "roots", "stable_a", "delay_price"]


def curvature(eta, a, H):
    return 1.0 - (1.0 - eta * a) ** H


def stable_limit(tau):
    """Largest a = alpha*s for which x_{t+1} = x_t - a x_{t-tau} converges (exclusive)."""
    return 2.0 * math.sin(math.pi / (4 * tau + 2))


def roots(a, tau, lam=0.0):
    """All roots of z^(tau+1) - (1 - lam a) z^tau + (1 - lam) a (Durand-Kerner); lam = 0 is the naive stale update."""
    n = tau + 1
    if n == 1:
        return [complex(1 - a)]
    rs = [cmath.rect(0.95, 2 * math.pi * (k + 0.37) / n) for k in range(n)]
    f = lambda z: z ** tau * (z - (1 - lam * a)) + (1 - lam) * a
    for _ in range(2000):
        delta = 0.0
        for k in range(n):
            den = 1.0
            for j in range(n):
                if j != k:
                    den *= rs[k] - rs[j]
            step = f(rs[k]) / den if den != 0 else 1e-8
            rs[k] -= step
            delta = max(delta, abs(step))
        if delta < 1e-15:
            break
    return rs


def radius(a, tau, lam=0.0):
    """Spectral radius (per-round contraction) of a mode with a = alpha*s at delay tau (exact roots)."""
    return max(abs(z) for z in roots(a, tau, lam))


def stable_a(tau, lam=0.0, a_cap=4.0, step=0.01):
    """Sup of a = alpha*s with radius < 1 (first crossing, by scan then bisection); closed form when lam = 0."""
    if lam == 0.0:
        return stable_limit(tau)
    lo = step
    while lo < a_cap and radius(lo, tau, lam) < 1.0 - 1e-9:
        lo += step
    if lo >= a_cap:
        return a_cap
    a, b = lo - step, lo
    for _ in range(40):
        m = (a + b) / 2
        a, b = (m, b) if radius(m, tau, lam) < 1.0 - 1e-9 else (a, m)
    return (a + b) / 2


def delay_price(tau):
    """(tau+1) * stable_limit(tau): rounds-in-flight gained times step-size cap paid; 2 at tau = 0, 1, then falls to pi/2."""
    return (tau + 1) * stable_limit(tau)


def single_optimal(tau):
    """(a*, radius*) minimising the radius of one mode; tau = 0 gives (1, 0): one step solves it."""
    if tau == 0:
        return 1.0, 0.0
    return tau ** tau / (tau + 1) ** (tau + 1), tau / (tau + 1)


def rate(ss, alpha, tau, lam=0.0):
    """Contraction of the whole quadratic = worst mode."""
    return max(radius(alpha * s, tau, lam) for s in ss)


def best_alpha(s_min, s_max, tau, iters=60, lam=0.0):
    """Outer step minimising the worst-mode radius over [s_min, s_max] (worst mode is an endpoint; golden section).
    Returns (alpha, rate)."""
    hi = stable_a(tau, lam) / s_max
    lo = 0.0
    g = (math.sqrt(5) - 1) / 2
    f = lambda al: max(radius(al * s_min, tau, lam), radius(al * s_max, tau, lam))
    a, b = lo, hi
    c, d = b - g * (b - a), a + g * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(iters):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - g * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + g * (b - a)
            fd = f(d)
    al = (a + b) / 2
    return al, f(al)


def rounds(rho, eps):
    return 0.0 if rho <= 0 else math.log(eps) / math.log(rho)


def period(H, C, tau):
    """Time per round when tau+1 rounds are in flight and a sync costs C."""
    return max(float(H), (H + C) / (tau + 1))


def wallclock(kappa, H, C, tau, eps, lam=0.0):
    """Time to eps with eta = 1/a_max and the tuned delayed outer step."""
    s_min, s_max = curvature(1.0, 1.0 / kappa, H), 1.0
    _, rho = best_alpha(s_min, s_max, tau, lam=lam)
    return rounds(rho, eps) * period(H, C, tau)


def best_design(kappa, C, eps, Hs, taus, lam=0.0):
    """(H, tau, time) minimising wallclock over the given grids."""
    return min(((H, t, wallclock(kappa, H, C, t, eps, lam)) for H in Hs for t in taus), key=lambda p: p[2])


def simulate(a_list, eta, H, alpha, tau, n_rounds, lam=0.0):
    """Literal simulation: each round runs H inner steps from the current global point, forms the pseudo-gradient,
    and the outer step applies the pseudo-gradient from tau rounds ago plus lam times the curvature-scaled drift since
    (history is the initial point). |x| per round."""
    x0 = [1.0] * len(a_list)
    hist = [list(x0)]                     # global points; hist[t] = x_t
    grads = []                            # pseudo-gradients g_t
    out = [math.sqrt(len(a_list))]
    for t in range(n_rounds):
        xt = hist[-1]
        g = []
        for i, a in enumerate(a_list):
            y = xt[i]
            for _ in range(H):
                y -= eta * a * y
            g.append(xt[i] - y)
        grads.append(g)
        old = grads[t - tau] if t - tau >= 0 else [s * x0[i] for i, s in enumerate(
            [curvature(eta, a, H) for a in a_list])]
        xold = hist[t - tau] if t - tau >= 0 else x0
        sv = [curvature(eta, a, H) for a in a_list]
        hist.append([xt[i] - alpha * (old[i] + lam * sv[i] * (xt[i] - xold[i])) for i in range(len(a_list))])
        out.append(math.sqrt(sum(v * v for v in hist[-1])))
    return out


def measured_rate(trace, window):
    """Geometric per-round rate from the max of |x| over the last two windows (robust to oscillation)."""
    n = len(trace)
    late = max(trace[n - window:])
    early = max(trace[n - 2 * window:n - window])
    return (late / early) ** (1.0 / window)
