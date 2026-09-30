import unittest

from flex_twin.model import (char_poly, roots, abscissa, routh_stable, design, max_stable_wn, wn_star, zs_required,
                             simulate)


class T(unittest.TestCase):
    def test_roots_of_known_polynomial(self):
        z = sorted(roots([1, -10, 35, -50, 24]), key=lambda c: c.real)   # (s-1)(s-2)(s-3)(s-4)
        for a, b in zip(z, (1, 2, 3, 4)):
            self.assertAlmostEqual(a.real, b, places=8)

    def test_twin_always_stable(self):
        for w in (0.01, 1, 30):
            kp, kd = design(w)
            self.assertGreater(kd, 0)
            self.assertGreater(kp, 0)   # J s^2 + kd s + kp, positive coefficients

    def test_closed_form_matches_bisection(self):
        for r in (0.3, 1, 4):
            for zs in (0.02, 0.1, 0.3):
                for zeta in (0.5, 0.7, 1.0):
                    self.assertAlmostEqual(max_stable_wn(r, zs, zeta) / wn_star(zs, zeta), 1, places=5)

    def test_routh_agrees_with_roots(self):
        for wn in (0.5 * wn_star(0.05), 0.99 * wn_star(0.05), 1.01 * wn_star(0.05), 3 * wn_star(0.05)):
            kp, kd = design(wn)
            self.assertEqual(routh_stable(1.0, 0.05, kp, kd), abscissa(char_poly(1.0, 0.05, kp, kd)) < 0)

    def test_undamped_never_stable(self):
        for wn in (0.001, 0.1, 1.0):
            kp, kd = design(wn)
            self.assertGreaterEqual(abscissa(char_poly(1.0, 0.0, kp, kd)), -1e-12)

    def test_collocated_stable_at_any_gain(self):
        for wn in (0.1, 1, 10, 50):
            kp, kd = design(wn)
            self.assertLess(abscissa(char_poly(1.0, 0.05, kp, kd, collocated=True)), 0)

    def test_inverse_relation(self):
        self.assertAlmostEqual(wn_star(zs_required(0.3)), 0.3, places=9)

    def test_simulation_matches_boundary(self):
        for f, grows in ((0.8, False), (1.25, True)):
            kp, kd = design(f * wn_star(0.2))
            y = simulate(1.0, 0.2, kp, kd, 600, dt=0.02)
            big = max(abs(v) for v in y[-2000:]) > max(abs(v) for v in y[2000:4000])
            self.assertEqual(big, grows)


if __name__ == "__main__":
    unittest.main()
