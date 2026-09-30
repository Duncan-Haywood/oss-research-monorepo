"""A target moves at speed v along an axis. Sensor A (reference clock) and sensor B (radar vs lidar, or two robots)
each report its position with independent N(0, sigma^2) noise. In the real system B's timestamp is off by delta, so B
reports the position at the wrong time: error v*delta. The twin has delta = 0; reality has delta ~ N(0, s^2) per scan
(jitter) or delta = d0 (constant calibration offset).

Association gate: A and B detections are associated if |zB - zA| < g. Fusion: (1-w) zA + w zB.
"""
import math, random
from statistics import NormalDist

__all__ = ["Phi", "zq", "design_gate", "diff_var", "kappa", "recall_jitter", "recall_bias", "speed_at_recall",
           "gate_repair", "neighbour_assoc", "fused_mse", "w_opt", "mse_opt", "sim_diffs", "sim_fused_mse"]

_N = NormalDist()


def Phi(x):
    return _N.cdf(x)


def zq(p):
    return _N.inv_cdf(p)


def design_gate(sigma, recall):
    """Gate the twin (delta = 0) picks for a target recall: difference is N(0, 2 sigma^2)."""
    return zq((1 + recall) / 2) * math.sqrt(2) * sigma


def diff_var(sigma, v, s):
    """Var(zB - zA) under timestamp jitter with sd s."""
    return 2 * sigma ** 2 + (v * s) ** 2


def kappa(sigma, v, s):
    """Variance inflation of the A-B difference relative to the twin's, and of the equal-weight fused MSE."""
    return 1 + (v * s) ** 2 / (2 * sigma ** 2)


def recall_jitter(g, sigma, v, s):
    """P(true pair associated) with jittered timestamps (exact)."""
    return 2 * Phi(g / math.sqrt(diff_var(sigma, v, s))) - 1


def recall_bias(g, sigma, v, d0):
    """P(true pair associated) with a constant offset d0 (exact): difference is N(v d0, 2 sigma^2)."""
    sd = math.sqrt(2) * sigma
    return Phi((g - v * d0) / sd) - Phi((-g - v * d0) / sd)


def speed_at_recall(g, sigma, s, target):
    """Speed at which a gate g has recall `target` under jitter s (0 if the twin's own recall is already below target)."""
    z = zq((1 + target) / 2)
    r = (g / z) ** 2 - 2 * sigma ** 2
    return math.sqrt(r) / s if r > 0 else 0.0


def gate_repair(sigma, v, s, recall):
    """Gate that restores the recall at speed v: inflate by sqrt(kappa)."""
    return zq((1 + recall) / 2) * math.sqrt(diff_var(sigma, v, s))


def neighbour_assoc(g, D, sigma, v, s):
    """P(a second target at true separation D, moving alike, falls inside the gate): the cost of a wider gate."""
    sd = math.sqrt(diff_var(sigma, v, s))
    return Phi((g - D) / sd) - Phi((-g - D) / sd)


def fused_mse(sigma, v, s, w):
    """MSE of (1-w) zA + w zB at the reference time, jitter s: (1-w)^2 sigma^2 + w^2 (sigma^2 + v^2 s^2)."""
    return (1 - w) ** 2 * sigma ** 2 + w ** 2 * (sigma ** 2 + (v * s) ** 2)


def w_opt(sigma, v, s):
    return sigma ** 2 / (2 * sigma ** 2 + (v * s) ** 2)


def mse_opt(sigma, v, s):
    return sigma ** 2 * (sigma ** 2 + (v * s) ** 2) / (2 * sigma ** 2 + (v * s) ** 2)


def sim_diffs(rng, sigma, v, s, n):
    """n simulated (zA - x, zB - x) error pairs with jittered timestamps."""
    out = []
    for _ in range(n):
        ea = sigma * rng.gauss(0, 1)
        eb = sigma * rng.gauss(0, 1) + v * s * rng.gauss(0, 1)
        out.append((ea, eb))
    return out


def sim_fused_mse(rng, sigma, v, s, w, n):
    return sum(((1 - w) * a + w * b) ** 2 for a, b in sim_diffs(rng, sigma, v, s, n)) / n
