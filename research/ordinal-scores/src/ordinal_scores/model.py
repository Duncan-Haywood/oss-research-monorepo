"""Ranked probability score (RPS) for ordinal K-bin verifier reports.

Outcome y in {0..K-1} (e.g. binned drift magnitude), report r on the simplex, CDF R_k = sum_{j<=k} r_j.
  rps    sum_{k<K-1} w_k (R_k - 1[y<=k])^2      unweighted range K-1
  brier  sum_j (r_j - 1[j=y])^2                  range 2, ignores bin order
"""
import math

__all__ = ["cdf", "rps_loss", "brier_loss", "exp_loss", "regret", "rps_regret", "brier_regret",
           "threshold_brier", "max_regret_rps", "max_regret_brier", "curv_rps", "curv_brier",
           "shift", "blur", "decision_regret", "uniform"]


def cdf(p):
    out, s = [], 0.0
    for x in p:
        s += x
        out.append(s)
    return out[:-1]  # last CDF value is 1 for any report


def rps_loss(r, y, w=None):
    R = cdf(r)
    w = w or [1.0] * len(R)
    return sum(wk * (Rk - (y <= k)) ** 2 for k, (Rk, wk) in enumerate(zip(R, w)))


def brier_loss(r, y):
    return sum((x - (j == y)) ** 2 for j, x in enumerate(r))


def exp_loss(loss, r, p):
    return sum(pj * loss(r, j) for j, pj in enumerate(p))


def regret(loss, r, p):
    return exp_loss(loss, r, p) - exp_loss(loss, p, p)


def rps_regret(r, p, w=None):
    """exact: sum_k w_k (R_k - P_k)^2"""
    R, P = cdf(r), cdf(p)
    w = w or [1.0] * len(R)
    return sum(wk * (a - b) ** 2 for wk, a, b in zip(w, R, P))


def brier_regret(r, p):
    return sum((a - b) ** 2 for a, b in zip(r, p))


def threshold_brier(r, y, k):
    """binary Brier score for the event {y <= k}; RPS is the sum of these over k"""
    return (cdf(r)[k] - (y <= k)) ** 2


def max_regret_rps(p):
    """convex in r, so the max over the simplex is at a vertex e_j: sum_k (P_k - 1[j<=k])^2"""
    P = cdf(p)
    return max(sum((Pk - (j <= k)) ** 2 for k, Pk in enumerate(P)) for j in range(len(p)))


def max_regret_brier(p):
    return 1 - 2 * min(p) + sum(x * x for x in p)


def curv_rps(d, w=None):
    """second-order regret for a perturbation d, sum(d)=0: sum_k w_k (cumsum d)_k^2"""
    D = cdf(d)
    w = w or [1.0] * len(D)
    return sum(wk * x * x for wk, x in zip(w, D))


def curv_brier(d):
    return sum(x * x for x in d)


def shift(p, i, j, eps):
    r = list(p)
    r[i] -= eps
    r[j] += eps
    return r


def blur(p, a):
    """each bin sends mass a to each neighbour (edges keep it): a smoothed, order-aware misreport"""
    K = len(p)
    r = [0.0] * K
    for j, x in enumerate(p):
        for n in (j - 1, j + 1):
            if 0 <= n < K:
                r[n] += a * x
                r[j] -= a * x
        r[j] += x
    return r


def decision_regret(r, p, t):
    """accept iff P(y<=t) >= 1/2 (symmetric costs); regret of acting on r instead of p is |2P_t-1| if the
    decisions differ, else 0"""
    Rt, Pt = cdf(r)[t], cdf(p)[t]
    return abs(2 * Pt - 1) if (Rt >= .5) != (Pt >= .5) else 0.0


def uniform(K):
    return [1.0 / K] * K
