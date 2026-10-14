import math, pathlib, sys, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from selfrep_rodbeam import beam as b


class T(unittest.TestCase):
    def test_closed_form_steel(self):
        # P=2.5 N, L=0.405 m, d=8 mm steel: hand-computed 2.5*0.405^3/(48*200e9*2.0106e-10)
        self.assertAlmostEqual(b.deflection(2.5, 0.405, 200e9, 8e-3), 8.6e-5, delta=0.5e-5)

    def test_matched_diameter_gives_equal_deflection(self):
        for E in (3e9, 12e9, 60e9):
            d = b.matched_diameter(E)
            self.assertAlmostEqual(b.deflection(2.5, 0.4, E, d), b.deflection(2.5, 0.4, b.E_STEEL, b.D0), places=12)

    def test_tolerance_diameter_hits_tolerance(self):
        d = b.tolerance_diameter(2.5, 0.4, 12e9, 2e-4)
        self.assertAlmostEqual(b.deflection(2.5, 0.4, 12e9, d), 2e-4, places=10)

    def test_stiffer_is_less_deflection_and_scaling_laws(self):
        self.assertLess(b.deflection(1, .4, 200e9, 8e-3), b.deflection(1, .4, 12e9, 8e-3))
        self.assertAlmostEqual(b.deflection(1, .8, 1e9, 8e-3) / b.deflection(1, .4, 1e9, 8e-3), 8.0)
        self.assertAlmostEqual(b.deflection(1, .4, 1e9, 16e-3) / b.deflection(1, .4, 1e9, 8e-3), 1 / 16)

    def test_mass(self):
        self.assertAlmostEqual(b.rod_mass_g("steel", 0.35, 8e-3), 138.1, delta=0.5)   # matches selfrep-closure's 140 g


if __name__ == "__main__":
    unittest.main()
