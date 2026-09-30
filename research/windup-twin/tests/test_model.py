import math
import unittest

from windup_twin.model import (gains, twin_overshoot, exit_time, real_overshoot, clamped_overshoot, simulate,
                               overshoot_of)

U = 1.0


def x0_for(a, wn, zeta):
    return a * U / gains(wn, zeta)[0]


class T(unittest.TestCase):
    def test_twin_critical_damping_is_exp_minus_two(self):
        self.assertAlmostEqual(twin_overshoot(1.0, 1.0), math.exp(-2), places=9)

    def test_twin_formula_matches_simulation(self):
        for zeta in (0.3, 0.7, 1.0, 2.0):
            x0 = 1.0
            sim = overshoot_of(simulate(x0, U, 1.0, zeta, 60, 1e-3, "twin"), x0)
            self.assertAlmostEqual(sim, twin_overshoot(1.0, zeta), places=4)

    def test_unsaturated_start_equals_twin(self):
        for a in (0.3, 1.0):
            self.assertAlmostEqual(real_overshoot(x0_for(a, 1.0, 1.0), U, 1.0, 1.0), twin_overshoot(1.0, 1.0), places=12)
            self.assertIsNone(exit_time(x0_for(a, 1.0, 1.0), U, *gains(1.0, 1.0)))

    def test_exact_windup_overshoot_matches_simulation(self):
        for zeta in (0.3, 0.7, 1.0, 2.0):
            for a in (2.0, 5.0, 20.0):
                x0 = x0_for(a, 1.0, zeta)
                sim = overshoot_of(simulate(x0, U, 1.0, zeta, 60 + 4 * x0, 1e-3), x0)
                self.assertAlmostEqual(sim, real_overshoot(x0, U, 1.0, zeta), places=3)

    def test_windup_grows_with_depth_and_exceeds_twin(self):
        prev = twin_overshoot(1.0, 1.0)
        for a in (2, 5, 20, 100):
            cur = real_overshoot(x0_for(a, 1.0, 1.0), U, 1.0, 1.0)
            self.assertGreater(cur, prev)
            prev = cur

    def test_deep_saturation_limit(self):
        for zeta in (0.7, 1.0, 2.0):
            kp, ki = gains(1.0, zeta)
            x0 = 1e6 * U / kp
            self.assertAlmostEqual((1 - real_overshoot(x0, U, 1.0, zeta)) * ki * x0 / (kp * U), 1.0, places=3)

    def test_conditional_integration_replays_twin_from_U_over_kp(self):
        for zeta in (0.7, 1.0, 2.0):
            for a in (2.0, 20.0):
                x0 = x0_for(a, 1.0, zeta)
                sim = overshoot_of(simulate(x0, U, 1.0, zeta, 60 + 4 * x0, 1e-3, "clamp"), x0)
                self.assertAlmostEqual(sim, clamped_overshoot(x0, U, 1.0, zeta), places=3)

    def test_clamped_absolute_overshoot_independent_of_x0(self):
        vals = [clamped_overshoot(x0_for(a, 1.0, 1.0), U, 1.0, 1.0) * x0_for(a, 1.0, 1.0) for a in (2, 10, 1000)]
        self.assertAlmostEqual(vals[0], vals[2], places=12)
        self.assertAlmostEqual(vals[0], vals[1], places=12)

    def test_scale_invariance(self):
        a = real_overshoot(x0_for(7, 1.0, 1.0), U, 1.0, 1.0)
        b = real_overshoot(x0_for(7, 5.0, 1.0), U, 5.0, 1.0)
        self.assertAlmostEqual(a, b, places=12)


if __name__ == "__main__":
    unittest.main()
