import math
import random
import unittest

from sample_twin.model import (gains, trace_det, multipliers, spectral_radius, real_stable, eps_limit, mechanism,
                               hunt_angle, deadbeat_gains, step, step_rk4, twin_step, twin_overshoot, overshoot)


class T(unittest.TestCase):
    def test_discretisation_matches_rk4(self):
        for wn, z, Ts in ((1, 0.7, 0.3), (2, 0.4, 0.2), (0.5, 2.0, 1.0)):
            kp, kd = gains(wn, z)
            a = step(kp, kd, Ts, 1.0, 30)
            b = step_rk4(kp, kd, Ts, 1.0, 30, sub=100)
            self.assertLess(max(abs(p - q) for p, q in zip(a, b)), 1e-9)

    def test_window_matches_multipliers(self):
        bad = 0
        for z in (0.1, 0.3, 0.5, 0.7, 1.0, 2.0, 5.0):
            for f in (0.5, 0.9, 0.99, 1.01, 1.1, 2.0):
                kp, kd = gains(f * eps_limit(z), z)
                bad += real_stable(kp, kd, 1.0) != (spectral_radius(kp, kd, 1.0) < 1)
        self.assertEqual(bad, 0)

    def test_eps_limit_and_cap(self):
        self.assertEqual(eps_limit(0.5), 2.0)
        for z in (0.1, 0.3, 0.5, 0.8, 2.0, 10.0):
            self.assertLessEqual(eps_limit(z), 2.0)
        self.assertEqual((mechanism(0.3), mechanism(0.5), mechanism(0.9)), ("delay", "both", "derivative"))

    def test_no_stable_gain_above_cap(self):
        random.seed(1)
        for _ in range(20000):
            kp = math.exp(random.uniform(-3, 4))
            kd = math.exp(random.uniform(-3, 4))
            if kp >= 4.0:
                self.assertFalse(spectral_radius(kp, kd, 1.0) < 1)

    def test_delay_boundary_angle(self):
        eps = 0.8
        kp = eps * eps
        kd = kp / 2.0                  # delay boundary kd = kp T/2 (T = 1), i.e. zeta = eps/4
        z = multipliers(kp, kd, 1.0)[0]
        self.assertAlmostEqual(abs(z), 1.0, places=12)
        self.assertAlmostEqual(abs(cmath_arg(z)), hunt_angle(eps), places=12)

    def test_derivative_boundary_multiplier_minus_one(self):
        kp, kd = 0.3, 2.0
        self.assertAlmostEqual(min(multipliers(kp, kd, 1.0), key=lambda z: z.real).real, -1.0, places=12)

    def test_deadbeat(self):
        kp, kd = deadbeat_gains(0.1)
        self.assertLess(spectral_radius(kp, kd, 0.1), 1e-7)
        xs = step(kp, kd, 0.1, 1.0, 4)
        self.assertLess(abs(xs[1]), 1e-9)
        self.assertAlmostEqual(kp * 0.01, 1.0)

    def test_small_eps_approaches_twin(self):
        z = 0.7
        ref = twin_step(1.0, z, 0.01, 1.0, 3000)
        kp, kd = gains(1.0, z)
        xs = step(kp, kd, 0.01, 1.0, 3000)
        self.assertLess(max(abs(a - b) for a, b in zip(ref, xs)), 0.01)
        self.assertAlmostEqual(twin_overshoot(0.5), overshoot(twin_step(1.0, 0.5, 0.001, 1.0, 20000), 1.0), places=4)


def cmath_arg(z):
    import cmath
    return cmath.phase(z)


if __name__ == "__main__":
    unittest.main()
