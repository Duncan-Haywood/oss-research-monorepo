import math
import unittest

from sag_twin.model import (v_end, runtime_real, runtime_twin, runtime_numeric, efficiency, p_start, hover_power, max_payload)

V0, M, C, VC = 25.2, 1.44, 5.0, 19.8  # 6S pack, OCV 25.2 -> 18.0 V over 5 Ah, cutoff 19.8 V under load


class T(unittest.TestCase):
    def test_closed_form_vs_numeric(self):
        for R in (0.02, 0.05, 0.1, 0.2):
            for P in (100, 200, 300, 400):
                a = runtime_real(P, R, V0, M, C, VC)
                b = runtime_numeric(P, R, V0, M, C, VC, 40000)
                self.assertAlmostEqual(a, b, delta=2e-4 * max(a, 1e-3) + 2e-5)

    def test_zero_resistance_is_twin(self):
        for P in (50, 200, 500):
            self.assertAlmostEqual(runtime_real(P, 1e-12, V0, M, C, VC), runtime_twin(P, V0, M, C, VC), places=6)

    def test_energy_balance(self):
        # delivered energy P t equals int (v I - I^2 R) dt = int (v - I R) dx; midpoint-integrate and compare
        P, R, n = 300.0, 0.1, 100000
        ve = v_end(P, R, V0, M, C, VC)
        xe = (V0 - ve) / M
        h, e = xe / n, 0.0
        for i in range(n):
            v = V0 - M * (i + 0.5) * h
            i_a = (v - math.sqrt(v * v - 4 * R * P)) / (2 * R)
            e += (v - i_a * R) * h
        self.assertAlmostEqual(P * runtime_real(P, R, V0, M, C, VC), e, delta=1e-4 * e)

    def test_efficiency_below_one_and_monotone(self):
        for R in (0.05, 0.1):
            e = [efficiency(P, R, V0, M, C, VC) for P in range(50, 450, 25)]
            self.assertTrue(all(x < 1 for x in e))
            self.assertTrue(all(b < a for a, b in zip(e, e[1:])))

    def test_efficiency_monotone_in_resistance(self):
        e = [efficiency(300, R / 100, V0, M, C, VC) for R in range(1, 15)]
        self.assertTrue(all(b < a for a, b in zip(e, e[1:])))

    def test_start_limit(self):
        R = 0.1
        pm = p_start(R, V0, VC)
        self.assertGreater(runtime_real(pm * 0.999, R, V0, M, C, VC), 0)
        self.assertEqual(runtime_real(pm * 1.001, R, V0, M, C, VC), 0.0)
        self.assertAlmostEqual(runtime_real(pm, R, V0, M, C, VC), 0.0, places=9)

    def test_cutoff_is_a_sag_cliff_not_a_cliff_of_the_ocv(self):
        # at the end of the flight the terminal voltage equals the cutoff
        P, R = 300.0, 0.1
        ve = v_end(P, R, V0, M, C, VC)
        vt = (ve + math.sqrt(ve * ve - 4 * R * P)) / 2
        self.assertAlmostEqual(vt, VC, places=9)

    def test_capacity_limited_regime(self):
        # tiny R, low power: charge exhausted before the cutoff; real runtime = twin runtime up to a tiny loss
        r = runtime_real(50, 0.01, V0, 1.0, 2.0, VC)
        self.assertLess(r, runtime_twin(50, V0, 1.0, 2.0, VC))
        self.assertGreater(r, 0.99 * runtime_twin(50, V0, 1.0, 2.0, VC))

    def test_payload_twin_exceeds_real(self):
        tw = lambda P: runtime_twin(P, V0, M, C, VC)
        re = lambda P: runtime_real(P, 0.1, V0, M, C, VC)
        a = max_payload(0.2, 150.0, 1.0, tw)
        b = max_payload(0.2, 150.0, 1.0, re)
        self.assertGreater(a, b)
        # the bisection result sits on the boundary
        self.assertAlmostEqual(re(hover_power(1.0 + b, 150.0, 1.0)), 0.2, places=6)

    def test_hover_scaling(self):
        self.assertAlmostEqual(hover_power(4.0, 100.0, 1.0), 800.0)


if __name__ == "__main__":
    unittest.main()
