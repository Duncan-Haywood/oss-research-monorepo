"""Grip force of a two-finger grasp trained in a digital twin with a wrong friction law.
Static load L = m(g + a) is carried by two contacts, so the object slips iff 2 mu N < L, i.e. mu < L/(2N).
Real friction mu is lognormal(ln mu0, s). Cost J(N) = c_d P(slip) + c_f N (drop/damage cost, per-newton crush/energy cost).
Write N = N0 exp(-s z) with N0 = L/(2 mu0): then P(slip) = Phi(z) and J'(z) = c_d phi(z) - s c_f N0 exp(-s z), whose
interior minimiser is the closed form z* = s - sqrt(2 ln(1/(rho sqrt(2 pi)))), rho = s c_f N0 exp(-s^2/2)/c_d."""
import math, random

__all__ = ["Phi", "phi", "Phi_inv", "load", "p_slip", "cost", "z_star", "best_force", "twin_force", "real_drop",
           "real_cost", "regret", "brute_force_z", "simulate_grasp", "simulate_drop_rate", "predictive_drop",
           "delta_predictive_drop", "c4", "plugin_multiplier", "sample_plugin_drop"]


def Phi(x):
    return 0.5 * math.erfc(-x / math.sqrt(2))


def phi(x):
    return math.exp(-x * x / 2) / math.sqrt(2 * math.pi)


def Phi_inv(p):
    lo, hi = -40.0, 40.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if Phi(mid) < p: lo = mid
        else: hi = mid
    return (lo + hi) / 2


def load(m, a, g=9.81):
    """Peak tangential load on the two contacts for mass m lifted with acceleration a."""
    return m * (g + a)


def p_slip(N, L, mu0, s):
    """P(2 mu N < L) for lognormal(ln mu0, s) friction; s = 0 is the deterministic step."""
    if N <= 0: return 1.0
    x = math.log(L / (2 * N)) - math.log(mu0)
    if s == 0: return 1.0 if x > 0 else 0.0
    return Phi(x / s)


def cost(N, L, mu0, s, c_d, c_f):
    return c_d * p_slip(N, L, mu0, s) + c_f * N


def z_star(N0, s, c_d, c_f):
    """Interior minimiser z* (standardised slip quantile) or None if the interior root does not exist / is not better than not gripping."""
    rho = s * c_f * N0 * math.exp(-s * s / 2) / c_d
    arg = rho * math.sqrt(2 * math.pi)
    if arg >= 1: return None
    z = s - math.sqrt(2 * math.log(1 / arg))
    j = c_d * Phi(z) + c_f * N0 * math.exp(-s * z)
    return z if j < c_d else None


def best_force(L, mu0, s, c_d, c_f):
    """Cost-minimising grip force in a world with friction lognormal(ln mu0, s). Returns (N, J). s = 0 gives the corner N0 or 0."""
    N0 = L / (2 * mu0)
    if s == 0:
        return (N0, c_f * N0) if c_d > c_f * N0 else (0.0, c_d)
    z = z_star(N0, s, c_d, c_f)
    if z is None: return 0.0, c_d
    N = N0 * math.exp(-s * z)
    return N, cost(N, L, mu0, s, c_d, c_f)


def twin_force(L, mu_twin, s_twin, c_d, c_f):
    """Force the twin's optimiser picks (twin friction lognormal(ln mu_twin, s_twin); s_twin = 0 is a deterministic-friction twin)."""
    return best_force(L, mu_twin, s_twin, c_d, c_f)[0]


def real_drop(N, L, mu0, s):
    return p_slip(N, L, mu0, s)


def real_cost(N, L, mu0, s, c_d, c_f):
    return cost(N, L, mu0, s, c_d, c_f)


def regret(L, mu0, s, c_d, c_f, mu_twin, s_twin):
    """Real cost of the twin-trained force minus the real optimum."""
    Nt = twin_force(L, mu_twin, s_twin, c_d, c_f)
    return cost(Nt, L, mu0, s, c_d, c_f) - best_force(L, mu0, s, c_d, c_f)[1]


def brute_force_z(N0, s, c_d, c_f, lo=-8.0, hi=12.0, n=40000):
    """Grid minimiser of J(z) = c_d Phi(z) + c_f N0 exp(-s z), for checking z_star."""
    best = None
    for i in range(n + 1):
        z = lo + (hi - lo) * i / n
        j = c_d * Phi(z) + c_f * N0 * math.exp(-s * z)
        if best is None or j < best[1]: best = (z, j)
    return best


def simulate_grasp(N, mu, m, a_lift, T=0.5, dt=0.005, drop_disp=0.001, g=9.81):
    """Time-stepped Coulomb-friction grasp: gripper accelerates upward at a_lift for T seconds; friction on the object
    is capped at 2 mu N. Returns True if the object slips more than drop_disp relative to the gripper."""
    cap = 2 * mu * N
    v_rel = 0.0
    x_rel = 0.0
    for _ in range(int(round(T / dt))):
        need = m * (g + a_lift)          # friction needed for the object to follow the gripper
        if v_rel == 0.0 and need <= cap:
            continue
        # sliding: object acceleration = (cap - m g)/m, gripper's is a_lift; relative accel of object w.r.t. gripper
        a_rel = (cap - m * g) / m - a_lift
        v_rel += a_rel * dt
        x_rel += v_rel * dt
        if x_rel < -drop_disp: return True
    return False


def simulate_drop_rate(N, m, a_lift, mu0, s, n, seed=0, **kw):
    rng = random.Random(seed)
    return sum(simulate_grasp(N, math.exp(rng.gauss(math.log(mu0), s)), m, a_lift, **kw) for _ in range(n)) / n


# ---- finite real friction data: threshold = ybar + k * shat on ln mu from n real friction measurements ----
def c4(n):
    """E[shat]/s for the sample sd with n points."""
    return math.sqrt(2 / (n - 1)) * math.exp(math.lgamma(n / 2) - math.lgamma((n - 1) / 2))


def predictive_drop(n, k, steps=4000):
    """Exact E[P(slip)] when the force is set at the slip threshold ybar + k*shat (log friction) estimated from n i.i.d. real
    lognormal measurements: E_shat Phi(k shat/s / sqrt(1+1/n)), shat^2/s^2 ~ chi2_{n-1}/(n-1). Integrated by Simpson on w = ln(shat^2/s^2)."""
    d = n - 1
    lo, hi = -9.0, 4.0
    h = (hi - lo) / steps
    tot = 0.0
    for i in range(steps + 1):
        w = lo + i * h
        r = math.exp(w)  # shat^2/s^2
        # density of w: chi2 for X = d r, r = X/d; dX = d r dw
        X = d * r
        lg = (d / 2 - 1) * math.log(X) - X / 2 - (d / 2) * math.log(2) - math.lgamma(d / 2) + math.log(X)
        dens = math.exp(lg)
        f = dens * Phi(k * math.sqrt(r) / math.sqrt(1 + 1 / n))
        tot += f * (1 if i in (0, steps) else (4 if i % 2 else 2))
    return tot * h / 3


def delta_predictive_drop(n, delta):
    """Second-order approximation to the plug-in (k = z_delta) expected drop probability."""
    z = Phi_inv(delta)
    e1 = z * (c4(n) - 1)
    e2 = 1 / n + z * z * (1 - c4(n) ** 2) + e1 * e1
    return delta + phi(z) * e1 + 0.5 * (-z * phi(z)) * e2


def plugin_multiplier(n, delta):
    """k_n with predictive_drop(n, k_n) = delta (bisection); k_n < z_delta, i.e. more pessimistic than the plug-in quantile."""
    lo, hi = -12.0, 0.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if predictive_drop(n, mid) > delta: hi = mid
        else: lo = mid
    return (lo + hi) / 2


def sample_plugin_drop(n, k, reps, seed=0):
    """Monte Carlo of the same expectation, for checking predictive_drop (s = 1 wlog)."""
    rng = random.Random(seed)
    tot = 0.0
    for _ in range(reps):
        ys = [rng.gauss(0, 1) for _ in range(n)]
        yb = sum(ys) / n
        sh = math.sqrt(sum((y - yb) ** 2 for y in ys) / (n - 1))
        tot += Phi(yb + k * sh)
    return tot / reps
