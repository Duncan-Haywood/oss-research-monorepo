import math
import random
import unittest

from rain_twin.model import (lambertw, kappa, rain_rate, detect, r_d, kappa_star, p_detect, quantile_range, mean_range, mean_rain,
                             sample_rain, brier_deterministic, brier_calibrated)

R0, K, ALPHA, P, M = 20.0, 0.05, 1.0, 0.10, 8.0


class T(unittest.TestCase):
    def test_lambertw_inverse(self):
        for x in (1e-6, 0.1, 1.0, 2.5, 10.0, 1e3, 1e8):
            w = lambertw(x)
            self.assertAlmostEqual(w * math.exp(w) / x, 1.0, places=10)

    def test_lambertw_known(self):
        self.assertAlmostEqual(lambertw(math.e), 1.0, places=12)
        self.assertEqual(lambertw(0.0), 0.0)

    def test_r_d_fixed_point(self):
        for kap in (0.001, 0.05, 0.3, 2.0):
            r = r_d(kap, R0)
            self.assertAlmostEqual(r, R0 * math.exp(-kap * r / 2), places=10)

    def test_r_d_clear_air(self):
        self.assertEqual(r_d(0.0, R0), R0)

    def test_detect_boundary(self):
        kap = 0.1
        r = r_d(kap, R0)
        self.assertTrue(detect(r * 0.9999, kap, R0))
        self.assertFalse(detect(r * 1.0001, kap, R0))

    def test_detect_beyond_r0_never(self):
        self.assertFalse(detect(R0 * 1.01, 0.0, R0))

    def test_r_d_decreasing_convex(self):
        xs = [0.2 * i for i in range(1, 100)]
        vals = [r_d(2 * x / R0, R0) for x in xs]
        self.assertTrue(all(a > b for a, b in zip(vals, vals[1:])))
        self.assertTrue(all(vals[i - 1] - 2 * vals[i] + vals[i + 1] > 0 for i in range(1, len(vals) - 1)))

    def test_kappa_roundtrip(self):
        for R in (0.5, 5.0, 40.0):
            for a in (0.7, 1.0, 1.4):
                self.assertAlmostEqual(rain_rate(kappa(R, K, a), K, a), R, places=10)

    def test_kappa_star_is_boundary(self):
        r = 12.0
        kap = kappa_star(r, R0)
        self.assertAlmostEqual(r_d(kap, R0), r, places=9)

    def test_p_detect_monotone_and_bounds(self):
        ps = [p_detect(r, R0, K, ALPHA, P, M) for r in (1, 5, 10, 15, 19.9)]
        self.assertTrue(all(a >= b for a, b in zip(ps, ps[1:])))
        self.assertTrue(all(1 - P - 1e-9 <= x <= 1.0 for x in ps))
        self.assertEqual(p_detect(21.0, R0, K, ALPHA, P, M), 0.0)

    def test_p_detect_matches_monte_carlo(self):
        rng = random.Random(5)
        draws = [sample_rain(rng, P, M) for _ in range(60000)]
        for r in (6.0, 14.0, 19.0):
            mc = sum(detect(r, kappa(R, K, ALPHA), R0) for R in draws) / len(draws)
            self.assertAlmostEqual(mc, p_detect(r, R0, K, ALPHA, P, M), delta=0.006)

    def test_jensen_gap_positive(self):
        self.assertGreater(mean_range(R0, K, ALPHA, P, M, n=20000), r_d(kappa(mean_rain(P, M), K, ALPHA), R0))

    def test_mean_range_matches_monte_carlo(self):
        rng = random.Random(7)
        mc = sum(r_d(kappa(sample_rain(rng, P, M), K, ALPHA), R0) for _ in range(80000)) / 80000
        self.assertAlmostEqual(mc, mean_range(R0, K, ALPHA, P, M, n=20000), delta=0.02)

    def test_median_equivariance(self):
        p = 0.6
        mdn_R = -M * math.log(0.5 / p)
        self.assertAlmostEqual(quantile_range(0.5, R0, K, ALPHA, p, M), r_d(kappa(mdn_R, K, ALPHA), R0), places=6)

    def test_calibrated_beats_deterministic(self):
        rs = [2 + 18 * (i + 0.5) / 500 for i in range(500)]
        cal = brier_calibrated(rs, R0, K, ALPHA, P, M, P, M)
        for rt in (R0, r_d(kappa(P * M, K, ALPHA), R0), quantile_range(0.5, R0, K, ALPHA, P, M)):
            self.assertLess(cal, brier_deterministic(rs, R0, K, ALPHA, P, M, rt))

    def test_brier_proper(self):
        rs = [2 + 18 * (i + 0.5) / 500 for i in range(500)]
        cal = brier_calibrated(rs, R0, K, ALPHA, P, M, P, M)
        for pt, mt in ((0.05, M), (0.3, M), (P, 3.0), (P, 20.0)):
            self.assertGreater(brier_calibrated(rs, R0, K, ALPHA, P, M, pt, mt), cal)


if __name__ == "__main__":
    unittest.main()
