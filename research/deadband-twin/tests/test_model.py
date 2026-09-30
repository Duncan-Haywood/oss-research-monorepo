import random
import unittest

from deadband_twin.model import (deadband, p_active, plim_ols, simulate_id, ols_gain, fit_deadband, loop,
                                 floor_p, chatter_amp, basin_edge)


class T(unittest.TestCase):
    def test_deadband_shape(self):
        self.assertEqual(deadband(0.05, 0.1), 0.0)
        self.assertAlmostEqual(deadband(0.3, 0.1), 0.2)
        self.assertAlmostEqual(deadband(-0.3, 0.1), -0.2)
        self.assertEqual(p_active(0.0, 1.0), 1.0)

    def test_bussgang_gain(self):
        for sigma in (0.05, 0.1, 0.4):
            u, y = simulate_id(300000, 1.5, 0.1, sigma, 0.0, random.Random(1))
            self.assertAlmostEqual(ols_gain(u, y) / 1.5, p_active(0.1, sigma), delta=0.01)

    def test_p_floor_and_approach(self):
        b, d, K = 1.0, 0.1, 0.5
        tr = loop(b, d, K, steps=200)
        self.assertAlmostEqual(tr[-1], floor_p(d, K), places=9)
        self.assertTrue(all(t >= floor_p(d, K) for t in tr))

    def test_unstable_diverges(self):
        self.assertGreater(abs(loop(1.0, 0.1, 2.5, steps=200)[-1]), 1e3)  # e0=1 above the 0.2 basin edge

    def test_basin_edge_above_two(self):
        b, d, m = 1.0, 0.1, 2.5
        edge = basin_edge(b, d, m)
        self.assertAlmostEqual(edge, 0.2)
        self.assertLessEqual(abs(loop(b, d, m, e0=0.99 * edge, steps=400)[-1]), d / m + 1e-12)
        self.assertGreater(abs(loop(b, d, m, e0=1.01 * edge, steps=400)[-1]), 1e3)

    def test_overshoot_regime_stops_inside_zone(self):
        tr = loop(1.0, 0.1, 1.6, steps=200)
        self.assertLessEqual(abs(tr[-1]), floor_p(0.1, 1.6) + 1e-12)

    def test_inverse_compensation_asymmetry(self):
        b, d, K = 1.0, 0.1, 0.5
        under = loop(b, d, K, dh=d - 0.04, steps=400)[-1]
        self.assertAlmostEqual(abs(under), 0.04 / K, places=9)
        over = loop(b, d, K, dh=d + 0.04, steps=400)
        self.assertAlmostEqual(abs(over[-1]), chatter_amp(b, 0.04, b * K), places=9)
        self.assertAlmostEqual(over[-1], -over[-2], places=9)

    def test_fit_recovers_parameters(self):
        u, y = simulate_id(20000, 1.0, 0.1, 0.15, 0.02, random.Random(3))
        b, d = fit_deadband(u, y, [i * 0.005 for i in range(1, 41)])
        self.assertAlmostEqual(b, 1.0, delta=0.05)
        self.assertAlmostEqual(d, 0.1, delta=0.01)


if __name__ == "__main__":
    unittest.main()
