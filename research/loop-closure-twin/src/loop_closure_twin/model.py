"""Loop closure on a 1-D odometry chain, tuned in a digital twin.
A robot integrates n odometry increments u_i = d_i + eps_i (true pose x_k = sum_{i<=k} d_i) and then re-observes the start-relative
pose x_n with noise v (variance sc2); the residual is rho = v - S_n, S_n = sum eps_i. The mapper corrects pose k by a share h_k of rho:
    xhat_k = sum_{i<=k} u_i + h_k rho,   h_k = g k  (linear spreading, one gain g).
For ANY real increment-error covariance, with v_k = Var S_k, a_k = Cov(S_k, S_n) and W = a_n + sc2 = Var(rho), exactly
    Var(xhat_k - x_k) = v_k - 2 h_k a_k + h_k^2 W,       best h_k = a_k / W  (variance v_k - a_k^2/W).
Real errors here: eps_i = b_i + e_i with e_i iid N(0, sig2) and a drifting bias b_i = b_{i-1} + w_i, w_i iid N(0, q), b_0 = 0
(q = 0 is the twin's independent-noise world). A *constant* shared bias is a special case that linear spreading absorbs, see experiments.
The twin assumes independent increments of variance st2: gain g_t = st2/(n st2 + sc2), claimed Var_k = k st2 - k^2 st2^2/(n st2 + sc2)."""
import math, random, statistics

__all__ = ["Chain", "cov_terms", "real_var", "claimed_var", "gain_twin", "gain_end", "profile_opt", "worst",
           "worst_claimed", "max_length_claimed", "max_length_real", "nees_ratio", "nees_power", "simulate"]


class Chain:
    """n steps; sig2 independent per-step variance; q per-step variance of the bias random walk; sc2 loop-closure variance."""
    def __init__(self, n, sig2, q, sc2):
        self.n, self.sig2, self.q, self.sc2 = n, sig2, q, sc2

    def replace(self, **kw):
        d = dict(n=self.n, sig2=self.sig2, q=self.q, sc2=self.sc2)
        d.update(kw)
        return Chain(**d)


def cov_terms(ch):
    """(v, a) lists for k = 1..n: v_k = Var S_k, a_k = Cov(S_k, S_n). Cov(b_i, b_j) = q min(i, j)."""
    n = ch.n
    m = lambda i, j: min(i, j)
    v, a = [], []
    for k in range(1, n + 1):
        vk = k * ch.sig2 + ch.q * sum(m(i, j) for i in range(1, k + 1) for j in range(1, k + 1))
        ak = k * ch.sig2 + ch.q * sum(i * (i + 1) // 2 + i * (n - i) for i in range(1, k + 1))
        v.append(vk); a.append(ak)
    return v, a


def _W(ch, a):
    return a[-1] + ch.sc2


def real_var(ch, g, k, terms=None):
    """Exact error variance at pose k (1-based) under linear spreading h_k = g k."""
    v, a = terms or cov_terms(ch)
    return v[k - 1] - 2 * g * k * a[k - 1] + (g * k) ** 2 * _W(ch, a)


def profile_opt(ch, k, terms=None):
    """Error variance at pose k under the best per-pose share h_k = a_k / W (needs the real covariance)."""
    v, a = terms or cov_terms(ch)
    return v[k - 1] - a[k - 1] ** 2 / _W(ch, a)


def gain_twin(ch, st2):
    return st2 / (ch.n * st2 + ch.sc2)


def gain_end(ch):
    """Gain that is exactly optimal at the last pose: g = a_n / (n W) = (W - sc2)/(n W)."""
    _, a = cov_terms(ch)
    return a[-1] / (ch.n * _W(ch, a))


def claimed_var(ch, st2, k):
    return k * st2 - k * k * st2 * st2 / (ch.n * st2 + ch.sc2)


def worst(ch, g):
    t = cov_terms(ch)
    return max(real_var(ch, g, k, t) for k in range(1, ch.n + 1))


def worst_claimed(ch, st2):
    return max(claimed_var(ch, st2, k) for k in range(1, ch.n + 1))


def max_length_claimed(base, st2, tau2, nmax=300):
    """Largest n whose twin-claimed worst-pose variance is <= tau2 (the claim rises with n)."""
    best = 0
    for n in range(1, nmax + 1):
        if worst_claimed(base.replace(n=n), st2) <= tau2:
            best = n
        else:
            break
    return best


def max_length_real(base, tau2, gain, nmax=300):
    """Largest n whose real worst-pose variance <= tau2; gain(ch) returns the linear gain used at that length."""
    best = 0
    for n in range(1, nmax + 1):
        ch = base.replace(n=n)
        if worst(ch, gain(ch)) <= tau2:
            best = n
        else:
            break
    return best


def nees_ratio(ch, st2, k):
    """Real error variance over twin-claimed variance at pose k, under the twin's own gain (1 = consistent, > 1 = overconfident)."""
    return real_var(ch, gain_twin(ch, st2), k) / claimed_var(ch, st2, k)


def nees_power(ratio, m, rng, alpha=0.05, draws=20000):
    """Power of the one-sided audit 'mean of m squared errors / claimed variance > c_alpha' when the true ratio is `ratio`;
    c_alpha is the (1-alpha) quantile of chi2_m / m, both estimated by simulation."""
    def chi(m_):
        return sum(rng.gauss(0, 1) ** 2 for _ in range(m_)) / m_
    null = sorted(chi(m) for _ in range(draws))
    c = null[int((1 - alpha) * draws)]
    return sum(1 for _ in range(draws) if ratio * chi(m) > c) / draws, c


def simulate(ch, g, k, trials, rng):
    """Monte Carlo error variance at pose k, drawing the bias walk, iid noise and closure noise explicitly."""
    tot = 0.0
    for _ in range(trials):
        b, eps = 0.0, []
        for _ in range(ch.n):
            b += rng.gauss(0, math.sqrt(ch.q))
            eps.append(b + rng.gauss(0, math.sqrt(ch.sig2)))
        rho = rng.gauss(0, math.sqrt(ch.sc2)) - sum(eps)
        err = sum(eps[:k]) + g * k * rho
        tot += err * err
    return tot / trials
