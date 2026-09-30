import math
import random
import unittest

from drag_twin.model import *


def rk4(f, v, t_end, n=20000):
    h = t_end / n
    for _ in range(n):
        a = f(v); b = f(v + h * a / 2); c = f(v + h * b / 2); d = f(v + h * c)
        v += h * (a + 2 * b + 2 * c + d) / 6
    return v


class T(unittest.TestCase):
    def test_coast_matches_ode(self):
        k, v0 = 0.5, 10.0
        self.assertAlmostEqual(rk4(lambda v: -k * v * v, v0, 3.0), real_coast_speed(3.0, v0, k), places=8)

    def test_step_matches_ode(self):
        k, F, vs = 0.5, 8.0, 1.0
        self.assertAlmostEqual(rk4(lambda v: F - k * v * v, vs, 1.7), real_step_speed(1.7, vs, F, k), places=8)
        self.assertAlmostEqual(real_step_speed(0.0, vs, F, k), vs, places=12)

    def test_distance_and_time_consistent(self):
        k, v0, vf = 0.3, 9.0, 2.0
        t = real_time_to(vf, v0, k)
        self.assertAlmostEqual(real_coast_speed(t, v0, k), vf, places=12)
        self.assertAlmostEqual(math.log(1 + k * v0 * t) / k, real_dist_to(vf, v0, k), places=12)

    def test_twin_distance_finite_truth_unbounded(self):
        k, v0 = 0.5, 10.0
        self.assertLess(twin_dist_to(1e-9, v0, secant_c(k, v0)), v0 / (k * v0) + 1e-6)
        self.assertGreater(real_dist_to(1e-9, v0, k), 40)

    def test_secant_steady_state_exact_at_cal_speed(self):
        k, vc = 0.5, 6.0
        F = k * vc * vc
        self.assertAlmostEqual(terminal_twin(F, secant_c(k, vc)), terminal_real(F, k), places=12)

    def test_secant_time_constant_is_twice_real(self):
        k, vc = 0.5, 6.0
        F = k * vc * vc
        eps = 1e-3
        real = time_to_fraction(lambda t: real_step_speed(t, vc, F * (1 + eps), k), vc, terminal_real(F * (1 + eps), k))
        twin = time_to_fraction(lambda t: twin_step_speed(t, vc, F * (1 + eps), secant_c(k, vc)), vc, F * (1 + eps) / secant_c(k, vc))
        self.assertAlmostEqual(twin / real, 2.0, delta=0.01)

    def test_tangent_fixes_dynamics_not_steady_state(self):
        k, vc = 0.5, 6.0
        F = k * vc * vc
        c = tangent_c(k, vc)
        self.assertAlmostEqual(terminal_twin(F, c) / terminal_real(F, k), 0.5, places=12)

    def test_ls_fit_uniform_three_quarters(self):
        self.assertAlmostEqual(ls_force_fit_c(1.0, 4.0), 3.0, places=12)

    def test_energy_ratio_is_speed_ratio(self):
        k, vc = 0.5, 4.0
        c = secant_c(k, vc)
        self.assertAlmostEqual(energy_per_dist_twin(8.0, c) / energy_per_dist_real(8.0, k), vc / 8.0, places=12)

    def test_noisefree_fit_recovers_chord_not_secant(self):
        data = coast_data(10.0, 0.5, 0.01, 1.0, 0.0, random.Random(0))
        c = fit_c_from_speed(data)
        self.assertGreater(c, secant_c(0.5, 5.0) * 0.5)
        self.assertLess(c, tangent_c(0.5, 10.0))


if __name__ == "__main__":
    unittest.main()
