import math
import unittest

from sweep_twin.model import (walls_rectangle, cast, scan, sector, fit_line, wall_yaw, skew_formula, speed_limit, deskew,
                              deskew_residual, deskew_tolerance, room_heading, wrap)

T = 0.1
HW = math.radians(30)
ROOM = walls_rectangle(-5, 5, -5, 5)


class Tests(unittest.TestCase):
    def test_cast_hits_wall(self):
        self.assertAlmostEqual(cast(ROOM, (0, 0), 0.0, 0.0), 5.0, places=12)
        self.assertAlmostEqual(cast(ROOM, (1, 0), 0.0, math.pi), 6.0, places=12)
        self.assertAlmostEqual(cast(ROOM, (0, 0), 0.0, math.pi / 4), 5 * math.sqrt(2), places=12)

    def test_fit_line_recovers_wall(self):
        a, d = fit_line(sector(scan(ROOM, T=T), 0.0, HW))
        self.assertAlmostEqual(wrap(a), 0.0, places=12)
        self.assertAlmostEqual(d, 5.0, places=10)

    def test_twin_sees_no_skew(self):
        for c in (0.0, math.pi / 2, math.pi, -math.pi / 2):
            psi, _ = wall_yaw(scan(ROOM, T=T), c, HW)
            self.assertLess(abs(wrap(psi)), 1e-12)

    def test_skew_matches_first_order_formula(self):
        for v in (0.5, 1.0, 2.0):
            psi, d_fit = wall_yaw(scan(ROOM, v=(v, 0), T=T), 0.0, HW)
            self.assertAlmostEqual(psi, skew_formula(v, T, 5.0), delta=0.06 * skew_formula(v, T, 5.0))

    def test_skew_uses_distance_at_hit(self):
        v = 10.0
        psi, d_fit = wall_yaw(scan(ROOM, v=(v, 0), T=T), 0.0, HW)
        self.assertAlmostEqual(d_fit, 5.0 - v * T * 3 / 8, delta=0.02)          # wall x
        self.assertAlmostEqual(psi, skew_formula(v, T, d_fit), delta=0.1 * psi)

    def test_skew_linear_in_speed_and_period(self):
        p1, _ = wall_yaw(scan(ROOM, v=(1, 0), T=0.1), 0.0, HW)
        p2, _ = wall_yaw(scan(ROOM, v=(2, 0), T=0.1), 0.0, HW)
        p3, _ = wall_yaw(scan(ROOM, v=(1, 0), T=0.2), 0.0, HW)
        self.assertAlmostEqual(p2 / p1, 2.0, delta=0.03)
        self.assertAlmostEqual(p3 / p1, 2.0, delta=0.03)

    def test_tangential_velocity_does_not_skew(self):
        psi, _ = wall_yaw(scan(ROOM, v=(0, 10.0), T=T), 0.0, HW)
        self.assertLess(abs(psi), 1e-9)

    def test_only_normal_component_matters(self):
        a, _ = wall_yaw(scan(ROOM, v=(3, 0), T=T), 0.0, HW)
        b, _ = wall_yaw(scan(ROOM, v=(3, 7), T=T), 0.0, HW)
        self.assertAlmostEqual(a, b, delta=0.1 * abs(a))

    def test_back_wall_skews_opposite(self):
        room = walls_rectangle(-5, 5, -5, 5)
        pf, _ = wall_yaw(scan(room, v=(2, 0), T=T), 0.0, HW)
        pb, _ = wall_yaw(scan(room, v=(2, 0), T=T), math.pi, HW)
        self.assertGreater(pf, 0)
        self.assertLess(pb, 0)

    def test_deskew_with_true_velocity_removes_skew(self):
        v = (10.0, 0.0)
        psi, _ = fit_line(sector(deskew(scan(ROOM, v=v, T=T), v), 0.0, HW))
        self.assertLess(abs(wrap(psi)), 1e-9)

    def test_deskew_residual_scales_with_error(self):
        v = 10.0
        res = []
        for eps in (0.1, 0.2):
            pts = deskew(scan(ROOM, v=(v, 0), T=T), ((1 - eps) * v, 0))
            res.append(wrap(fit_line(sector(pts, 0.0, HW))[0]))
        self.assertAlmostEqual(res[1] / res[0], 2.0, delta=0.05)
        self.assertAlmostEqual(res[0], deskew_residual(v, 0.9 * v, T, 5.0), delta=0.4 * res[0])

    def test_speed_limit_and_tolerance_consistent(self):
        self.assertAlmostEqual(skew_formula(speed_limit(0.02, T, 5.0), T, 5.0), 0.02, places=12)
        self.assertAlmostEqual(deskew_tolerance(0.01, 10.0, T, 5.0) * abs(skew_formula(10.0, T, 5.0)), 0.01, places=12)

    def test_symmetric_room_heading_bias_cancels_asymmetric_does_not(self):
        sym = walls_rectangle(-5, 5, -5, 5)
        asym = walls_rectangle(-2, 18, -5, 5)
        cs = [0.0, math.pi / 2, math.pi, -math.pi / 2]
        e_sym, _ = room_heading(scan(sym, v=(5, 0), T=T), cs, HW)
        e_asym, _ = room_heading(scan(asym, v=(5, 0), T=T), cs, HW)
        self.assertLess(abs(e_sym), 0.1 * abs(e_asym))

    def test_yaw_rate_bends_wall_linearly(self):
        def sag(om):
            pts = sector(scan(ROOM, yaw_rate=om, T=T), 0.0, math.radians(20))
            a, d = fit_line(pts)
            return max(abs(x * math.cos(a) + y * math.sin(a) - d) for x, y, _ in pts)
        self.assertGreater(sag(1.0), 0)
        self.assertAlmostEqual(sag(2.0) / sag(1.0), 2.0, delta=0.1)


if __name__ == "__main__":
    unittest.main()
