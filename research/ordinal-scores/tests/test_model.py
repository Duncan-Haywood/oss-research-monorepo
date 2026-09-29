import math, random, unittest
from ordinal_scores import *


def rp(K, rng):
    v = [rng.random() + 1e-3 for _ in range(K)]
    s = sum(v)
    return [x / s for x in v]


class T(unittest.TestCase):
    def test_regret_matches_enumeration(self):
        rng = random.Random(1)
        for _ in range(200):
            K = rng.randint(2, 8)
            p, r = rp(K, rng), rp(K, rng)
            w = [rng.random() for _ in range(K - 1)]
            self.assertAlmostEqual(regret(lambda a, y: rps_loss(a, y, w), r, p), rps_regret(r, p, w), 12)
            self.assertAlmostEqual(regret(brier_loss, r, p), brier_regret(r, p), 12)
            self.assertGreater(rps_regret(r, p), 0)

    def test_threshold_decomposition(self):
        rng = random.Random(2)
        for _ in range(100):
            K = rng.randint(2, 8)
            r = rp(K, rng)
            y = rng.randrange(K)
            self.assertAlmostEqual(rps_loss(r, y), sum(threshold_brier(r, y, k) for k in range(K - 1)), 12)

    def test_range(self):
        for K in (2, 5, 9):
            e0, eL = [1.0] + [0.0] * (K - 1), [0.0] * (K - 1) + [1.0]
            self.assertAlmostEqual(rps_loss(e0, K - 1), K - 1)
            self.assertAlmostEqual(rps_loss(eL, K - 1), 0)

    def test_curvature_distance(self):
        K, eps = 7, 1e-3
        p = uniform(K)
        for d in range(1, K):
            r = shift(p, 0, d, eps)
            self.assertAlmostEqual(rps_regret(r, p) / eps ** 2, d, 9)
            self.assertAlmostEqual(brier_regret(r, p) / eps ** 2, 2, 9)
            self.assertAlmostEqual(curv_rps([-1] + [0] * (d - 1) + [1] + [0] * (K - d - 1)), d)

    def test_max_regret(self):
        rng = random.Random(3)
        for _ in range(50):
            K = rng.randint(2, 6)
            p = rp(K, rng)
            m, mb = max_regret_rps(p), max_regret_brier(p)
            for _ in range(300):
                r = rp(K, rng)
                self.assertLessEqual(rps_regret(r, p), m + 1e-12)
                self.assertLessEqual(brier_regret(r, p), mb + 1e-12)
            v = [0.0] * K
            j = max(range(K), key=lambda j: sum((c - (j <= k)) ** 2 for k, c in enumerate(cdf(p))))
            v[j] = 1.0
            self.assertAlmostEqual(rps_regret(v, p), m, 12)

    def test_decision_transfer(self):
        rng = random.Random(4)
        for _ in range(3000):
            K = rng.randint(2, 7)
            p, r = rp(K, rng), rp(K, rng)
            t = rng.randrange(K - 1)
            w = [0.0] * (K - 1)
            w[t] = 1.0
            self.assertLessEqual(decision_regret(r, p, t), 2 * math.sqrt(rps_regret(r, p, w)) + 1e-12)

    def test_blur_mass(self):
        p = [.1, .2, .3, .25, .15]
        self.assertAlmostEqual(sum(blur(p, .2)), 1.0)
        self.assertGreater(rps_regret(blur(p, .2), p), 0)


if __name__ == "__main__":
    unittest.main()
