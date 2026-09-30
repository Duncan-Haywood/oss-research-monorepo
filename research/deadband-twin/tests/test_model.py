import math
import random
import unittest

from deadband_twin.model import (dead, q2, plim_gain, var_dead, sine_gain, simulate, ols, r2_line, fit_deadband,
                                 stall_error)


class T(unittest.TestCase):
    def test_dead_shape(self):
        self.assertEqual(dead(0.3, 0.5), 0.0)
        self.assertAlmostEqual(dead(1.0, 0.5), 0.5)
        self.assertAlmostEqual(dead(-1.0, 0.5), -0.5)
        self.assertEqual(q2(0.0), 1.0)

    def test_gain_is_probability_outside_deadband(self):
        for d in (0.25, 1.0, 1.5):
            u, y = simulate(400000, 1.5, d, 1.0, 0.0, random.Random(1))
            self.assertAlmostEqual(ols(u, y), plim_gain(1.5, d, 1.0), delta=0.01)

    def test_variance_formula(self):
        u, y = simulate(400000, 1.0, 0.7, 1.3, 0.0, random.Random(2))
        m = sum(y) / len(y)
        v = sum((t - m) ** 2 for t in y) / (len(y) - 1)
        self.assertAlmostEqual(v / var_dead(0.7, 1.3), 1.0, delta=0.02)

    def test_sine_gain_matches_numeric_fundamental(self):
        delta, amp, n = 0.5, 1.2, 20000
        s = sum(dead(amp * math.sin(2 * math.pi * k / n), delta) * math.sin(2 * math.pi * k / n) for k in range(n))
        self.assertAlmostEqual(2 * s / n / amp, sine_gain(delta, amp), places=3)
        self.assertEqual(sine_gain(0.5, 0.4), 0.0)

    def test_stall_band(self):
        self.assertAlmostEqual(stall_error(3.0, 1.0, 0.4), 0.4)
        for k in (0.3, 0.8, 1.5):
            for e0 in (0.2, 1.0, 4.0):
                self.assertLessEqual(abs(stall_error(e0, k, 0.4)), 0.4 / k + 1e-12)

    def test_deadband_fit_recovers_parameters(self):
        u, y = simulate(4000, 1.2, 0.6, 1.0, 0.1, random.Random(3))
        g, dl = fit_deadband(u, y)
        self.assertAlmostEqual(g, 1.2, delta=0.05)
        self.assertAlmostEqual(dl, 0.6, delta=0.05)
        b = ols(u, y)
        self.assertGreater(r2_line(u, y, b), 0.7)  # linear twin still looks fine


if __name__ == "__main__":
    unittest.main()
