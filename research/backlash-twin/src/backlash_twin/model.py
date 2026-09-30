"""Backlash twin.  Motor position m is integrated from the tracking error, m+ = m + K*(r - x); the load x is coupled to the
motor through gear play of half-width d.  With gap g = m - x in [-d, d] the load is at rest; the gap can only be closed
(contact, g = +-d) by driving the motor through it, after which the load follows the motor one-for-one.
Twin: x = m (no play).  Reference: square wave r = +A/2 for P steps, then -A/2 for P steps, repeating.

Exact facts derived here (all checked against simulation in tests/):
* symmetric limit cycle: load swings +-a; each half-period the load is stuck for n steps (error e0 = A/2 + a constant),
  n = ceil(2d/(K e0)), then it follows the motor.  a solves  a(1+q) = (A/2)(1-q) - 2 d c,  c=(1-K)^(P-n), q=c(1-nK);
* the twin swings +-(A/2)(1-rho)/(1+rho), rho=(1-K)^P;
* a load that never moves is also a solution iff K P A/2 <= 2d (motor excursion fits in the play).
"""
import math


def step(x, g, K, d, r):
    """One step of the real loop: returns (x, g)."""
    g2 = g + K * (r - x)
    if g2 > d:
        return x + g2 - d, d
    if g2 < -d:
        return x + g2 + d, -d
    return x, g2


def twin_step(x, K, r):
    return x + K * (r - x)


def reference(k, A, P):
    return A / 2 if (k // P) % 2 == 0 else -A / 2


def simulate(K, d, P, A, periods=200, x0=0.0, g0=0.0):
    """Returns list of (r, x) with x the load position before each step, over `periods` full periods (2P steps each)."""
    x, g, out = x0, g0, []
    for k in range(2 * P * periods):
        r = reference(k, A, P)
        out.append((r, x))
        x, g = step(x, g, K, d, r)
    return out


def simulate_twin(K, P, A, periods=200, x0=0.0):
    x, out = x0, []
    for k in range(2 * P * periods):
        r = reference(k, A, P)
        out.append((r, x))
        x = twin_step(x, K, r)
    return out


def twin_amplitude(K, P, A):
    rho = (1 - K) ** P
    return A / 2 * (1 - rho) / (1 + rho)


def twin_rms_error(K, P, A):
    """Exact stationary rms tracking error of the linear twin over one full period (symmetric cycle)."""
    a = twin_amplitude(K, P, A)
    s, e = 0.0, A / 2 + a
    for _ in range(P):
        s += e * e
        e *= 1 - K
    return math.sqrt(s / P)


def cycle_candidates(K, d, P, A):
    """All symmetric moving limit cycles (n, a): n stuck steps per half-period, swing +-a."""
    out = []
    for n in range(1, P + 1):
        c = (1 - K) ** (P - n)
        q = c * (1 - n * K)
        a = (A / 2 * (1 - q) - 2 * d * c) / (1 + q)
        e0 = A / 2 + a
        if a >= 0 and (n - 1) * K * e0 <= 2 * d < n * K * e0:
            out.append((n, a))
    return out


def stuck_possible(K, d, P, A):
    """A load that never moves (x = 0) is consistent iff the motor excursion K P A/2 fits in the play 2d."""
    return K * P * A / 2 <= 2 * d


def cycle_error_rms(K, d, P, A, n, a):
    """Exact rms tracking error over a half-period of the symmetric limit cycle (n, a)."""
    e0 = A / 2 + a
    total = n * e0 ** 2
    e = e0 * (1 - n * K) + 2 * d
    for _ in range(P - n):
        total += e * e
        e *= 1 - K
    return math.sqrt(total / P)


def measure(hist, P, periods=20):
    tail = hist[-2 * P * periods:]
    xs = [x for _, x in tail]
    rms = math.sqrt(sum((r - x) ** 2 for r, x in tail) / len(tail))
    return (max(xs) - min(xs)) / 2, rms
