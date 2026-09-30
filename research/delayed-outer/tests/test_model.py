import math, unittest
from delayed_outer import *


def grid(kap, n=40):
    return [kap ** (i / (n - 1)) / kap for i in range(n)]


class T(unittest.TestCase):
    def test_stability_limit_is_exact_boundary(self):
        for tau in range(0, 9):
            lim = stable_limit(tau)
            self.assertLess(radius(lim * 0.995, tau), 1.0)
            self.assertGreater(radius(lim * 1.005, tau), 1.0)
            self.assertAlmostEqual(radius(lim, tau), 1.0, places=6)
        self.assertAlmostEqual(stable_limit(0), 2.0)
        self.assertAlmostEqual(stable_limit(1), 1.0)

    def test_single_mode_optimum_is_double_root(self):
        for tau in range(1, 9):
            a, r = single_optimal(tau)
            self.assertAlmostEqual(radius(a, tau), r, places=5)
            for da in (-0.2, -0.05, 0.05, 0.2):
                self.assertGreaterEqual(radius(a * (1 + da), tau), r - 1e-9)

    def test_roots_satisfy_polynomial(self):
        for tau in (0, 2, 5):
            for z in roots(0.07, tau):
                self.assertLess(abs(z ** (tau + 1) - z ** tau + 0.07), 1e-9)

    def test_literal_simulation_matches_exact_rate(self):
        a_list = grid(100, 8)
        for H, tau in ((1, 2), (5, 3), (20, 1)):
            ss = [curvature(1.0, a, H) for a in a_list]
            al, rho = best_alpha(min(ss), max(ss), tau)
            n = min(3000, int(100 / -math.log(rho)) + 400)
            tr = simulate(a_list, 1.0, H, al, tau, n)
            self.assertAlmostEqual(measured_rate(tr, 100), rho, delta=3e-3)

    def test_plain_averaging_breaks_under_delay(self):
        # alpha = 1, s_max = 1 (eta a_max = 1): a = 1 is at the tau = 1 boundary and beyond it for tau >= 2
        self.assertAlmostEqual(radius(1.0, 1), 1.0, places=6)
        for tau in (2, 3, 6):
            self.assertGreater(radius(1.0, tau), 1.0)
        tr = simulate([1.0], 1.0, 1, 1.0, 3, 400)
        self.assertGreater(tr[-1], 1e3)

    def test_best_alpha_beats_grid_and_respects_limit(self):
        lo, hi = 0.05, 1.0
        for tau in (1, 3, 6):
            al, r = best_alpha(lo, hi, tau)
            self.assertLess(al * hi, stable_limit(tau))
            for k in range(1, 40):
                cand = stable_limit(tau) / hi * k / 40
                self.assertGreaterEqual(rate([lo, hi], cand, tau), r - 1e-6)

    def test_delay_never_speeds_convergence(self):
        lo = curvature(1.0, 0.01, 4)
        rs = [best_alpha(lo, 1.0, t)[1] for t in range(0, 8)]
        self.assertTrue(all(b >= a - 1e-12 for a, b in zip(rs, rs[1:])))

    def test_delay_price_and_compensation(self):
        p = [delay_price(t) for t in range(0, 30)]
        self.assertAlmostEqual(p[0], 2.0)
        self.assertAlmostEqual(p[1], 2.0)
        self.assertTrue(all(b < a for a, b in zip(p[1:], p[2:])))
        self.assertGreater(p[-1], math.pi / 2)
        for tau in (1, 4, 9):                           # lam = 1 removes the delay: roots 1-a and 0
            for a in (0.3, 1.0, 1.9):
                self.assertAlmostEqual(radius(a, tau, 1.0), abs(1 - a), places=6)
        tr = simulate([0.01, 1.0], 1.0, 1, 1.9, 5, 400, lam=1.0)
        self.assertAlmostEqual(measured_rate(tr, 100), abs(1 - 1.9 * 0.01), delta=2e-3)
        self.assertLess(stable_a(4, 2.0), stable_limit(0))   # over-estimated curvature tightens the cap

    def test_period_limits(self):
        self.assertEqual(period(10, 90, 0), 100.0)
        self.assertEqual(period(10, 90, 100), 10.0)
        self.assertAlmostEqual(period(10, 90, 4), 20.0)

    def test_compensated_overlap_helps_when_sync_is_expensive(self):
        Hs = [1, 2, 4, 8, 16, 32, 64, 128, 256]
        H0, t0, T0 = best_design(1000, 500, 1e-6, Hs, [0])
        H1, t1, T1 = best_design(1000, 500, 1e-6, Hs, range(0, 6), lam=1.0)
        self.assertLess(T1, T0)
        self.assertGreater(t1, 0)

    def test_naive_overlap_never_beats_blocking(self):
        for Hmax in ([1, 4, 16], [1, 4, 16, 64]):
            for C in (16, 256):
                T0 = best_design(1000, C, 1e-6, Hmax, [0])[2]
                T1 = best_design(1000, C, 1e-6, Hmax, [0, 1, 2, 4, 8])[2]
                self.assertGreaterEqual(T1, T0 * (1 - 1e-6))


if __name__ == "__main__":
    unittest.main()
