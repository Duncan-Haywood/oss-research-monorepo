import os, sys, math, random, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from anytime_audit import *

class T(unittest.TestCase):
    def test_kl(self):
        self.assertAlmostEqual(kl_bern(0.5, 0.5), 0)
        self.assertGreater(kl_bern(0.2, 0.05), 0)
    def test_mixture_is_martingale(self):
        # E under H0 of the next e-value equals the current one: check exactly at (k,n)=(3,10)
        a, k, n = 0.1, 3, 10
        nxt = a * math.exp(log_mixture(k + 1, n + 1, a)) + (1 - a) * math.exp(log_mixture(k, n + 1, a))
        self.assertAlmostEqual(nxt, math.exp(log_mixture(k, n, a)), places=9)
    def test_mixture_start(self):
        self.assertAlmostEqual(log_mixture(0, 0, 0.3), 0.0)
    def test_binom_sf(self):
        self.assertAlmostEqual(binom_sf(1, 3, 0.5), 0.875)
        self.assertAlmostEqual(binom_sf(0, 3, 0.5), 1.0)
    def test_threshold(self):
        k = fixed_n_threshold(100, 0.05, 0.05)
        self.assertLessEqual(binom_sf(k, 100, 0.05), 0.05); self.assertGreater(binom_sf(k - 1, 100, 0.05), 0.05)
    def test_ville_mixture_typeI(self):
        rng = random.Random(1)
        r, _ = rate(rng, lambda g: run_mixture(g, 0.05, 0.05, 0.05, 400), 1500)
        self.assertLessEqual(r, 0.05 + 0.02)
    def test_peeking_inflates(self):
        rng = random.Random(2)
        r, _ = rate(rng, lambda g: run_peeking(g, 0.05, 0.05, 0.05, 400), 600)
        self.assertGreater(r, 0.15)
    def test_sprt_speed(self):
        rng = random.Random(3)
        r, m = rate(rng, lambda g: run_sprt(g, 0.05, 0.2, 0.2, 0.01, 2000), 400)
        self.assertGreater(r, 0.98); self.assertLess(abs(m - math.log(100) / kl_bern(0.2, 0.05)) , 8)
if __name__ == "__main__": unittest.main()
