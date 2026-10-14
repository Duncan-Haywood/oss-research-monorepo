import math, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from selfrep_rodbeam import beam as b


class T(unittest.TestCase):
    def test_textbook_value(self):
        # F L^3/(48EI): 10 N, 0.4 m, steel 8 mm
        I = math.pi * 0.008 ** 4 / 64
        self.assertAlmostEqual(b.deflection(200e9, I, 0.4, 10) * 1e3,
                               10 * 0.4 ** 3 / (48 * 200e9 * I) * 1e3)

    def test_clamped_is_stiffer_by_4(self):
        I = b.inertia_solid(0.008)
        r = b.deflection(2e9, I, 0.4, 5) / b.deflection(2e9, I, 0.4, 5, "clamped")
        self.assertAlmostEqual(r, 4.0)

    def test_equal_stiffness_diameter(self):
        d = b.equal_stiffness_diameter(2e9, 200e9, 0.008)
        self.assertAlmostEqual(b.inertia_solid(d) * 2e9, b.inertia_solid(0.008) * 200e9, places=3)

    def test_min_diameter_inverts_deflection(self):
        d = b.min_passing_diameter(2.5e9, 0.4, 3.0, 1e-4)
        self.assertAlmostEqual(b.deflection(2.5e9, b.inertia_solid(d), 0.4, 3.0), 1e-4, places=12)

    def test_pass_probability_monotone_in_diameter(self):
        ps = [b.pass_probability("pla_printed", d, 0.4, 3.0, 1e-4) for d in (0.008, 0.016, 0.03)]
        self.assertEqual(ps, sorted(ps))

    def test_tube_matches_solid_when_hollow_zero(self):
        self.assertAlmostEqual(b.inertia_tube(0.01, 0.0), b.inertia_solid(0.01))


if __name__ == "__main__":
    unittest.main()
