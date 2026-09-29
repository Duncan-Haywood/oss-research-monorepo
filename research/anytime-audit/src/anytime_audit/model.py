"""Sequential audits of noisy checks. Each audited step flags with prob a (honest) or p>a (corrupted)."""
import math, random
from functools import lru_cache

def kl_bern(p, a):
    return p * math.log(p / a) + (1 - p) * math.log((1 - p) / (1 - a))

def log_lr_step(x, p, a):
    return math.log(p / a) if x else math.log((1 - p) / (1 - a))

def log_mixture(k, n, a):
    """log of the Beta(1,1)-mixture Bayes factor vs Bern(a) after k flags in n audits: a nonnegative
    martingale under H0, hence an e-process (Ville: P(sup E>=1/d)<=d)."""
    return math.lgamma(k + 1) + math.lgamma(n - k + 1) - math.lgamma(n + 2) - k * math.log(a) - (n - k) * math.log(1 - a)

def binom_sf(k, n, a):
    """P(Bin(n,a) >= k), exact."""
    if k <= 0: return 1.0
    lp = lambda j: math.lgamma(n + 1) - math.lgamma(j + 1) - math.lgamma(n - j + 1) + j * math.log(a) + (n - j) * math.log(1 - a)
    return min(1.0, sum(math.exp(lp(j)) for j in range(k, n + 1)))

@lru_cache(maxsize=None)
def fixed_n_threshold(n, a, delta):
    """smallest k with P(Bin(n,a)>=k)<=delta"""
    k = int(n * a)  # P(Bin>=k) > delta for k at or below the mean (delta<1/2)
    while binom_sf(k, n, a) > delta: k += 1
    return k

def fixed_n_needed(a, p, delta, power=0.8):
    """smallest n whose exact level-delta test has the given power against p"""
    n = 1
    while True:
        k = fixed_n_threshold(n, a, delta)
        if k <= n and binom_sf(k, n, p) >= power: return n
        n = n + 1 if n < 60 else int(n * 1.05) + 1

def run_sprt(rng, a, p_true, p1, delta, N):
    """returns audits until rejection (None if none by N); SPRT with alternative p1, threshold 1/delta"""
    L, thr = 0.0, math.log(1 / delta)
    for t in range(1, N + 1):
        L += log_lr_step(rng.random() < p_true, p1, a)
        if L >= thr: return t
    return None

def run_mixture(rng, a, p_true, delta, N):
    k, thr = 0, math.log(1 / delta)
    for t in range(1, N + 1):
        k += rng.random() < p_true
        if log_mixture(k, t, a) >= thr: return t
    return None

def run_peeking(rng, a, p_true, delta, N, every=1):
    """naive: re-run the fixed-n exact test at every `every` audits, reject at first significance"""
    k = 0
    for t in range(1, N + 1):
        k += rng.random() < p_true
        if t % every: continue
        if k >= fixed_n_threshold(t, a, delta): return t
    return None

def rate(rng, fn, reps):
    hits = [fn(rng) for _ in range(reps)]
    r = [h for h in hits if h is not None]
    return len(r) / reps, (sum(r) / len(r) if r else float("nan"))
