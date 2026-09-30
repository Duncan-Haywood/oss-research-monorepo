import unittest

from friction_twin.model import run_loop, twin_radius, amplitude, stick_slip_stats


class T(unittest.TestCase):
    def test_twin_is_linear_and_converges(self):
        xs, _ = run_loop(0.5, 0.1, 0.0, 0.0, 10.0, 400)
        self.assertLess(abs(xs[-1]), 1e-9)
        self.assertLess(twin_radius(0.5, 0.1), 1)

    def test_twin_radius_matches_simulation(self):
        self.assertAlmostEqual(twin_radius(0.5, 0.1), 0.5 ** 0.5, places=9)
        xs, _ = run_loop(0.3, 0.05, 0.0, 0.0, 1.0, 600)
        self.assertLess(abs(xs[-1]), 1e-6)

    def test_stick_below_breakaway(self):
        xs, sl = run_loop(0.5, 0.1, 10.0, 5.0, 1.0, 50)  # |u| stays far below fs at the start
        self.assertEqual(sl[0], 0)
        self.assertEqual(xs[0], 1.0)

    def test_equal_levels_come_to_rest(self):
        xs, _ = run_loop(0.5, 0.1, 1.0, 1.0, 10.0, 40000)
        self.assertLess(amplitude(xs), 1e-9)

    def test_stiction_drop_causes_hunting(self):
        xs, sl = run_loop(0.5, 0.1, 1.0, 0.5, 10.0, 40000)
        self.assertGreater(amplitude(xs), 0.3)
        self.assertGreater(stick_slip_stats(xs, sl)[0], 10)

    def test_exact_homogeneity(self):
        a = run_loop(0.5, 0.1, 1.0, 0.5, 10.0, 5000)[0]
        for lam in (2.0 ** -7, 2.0 ** 6):   # powers of two scale floats exactly, so the trajectories match bit for bit
            b = run_loop(0.5, 0.1, lam, 0.5 * lam, 10.0 * lam, 5000)[0]
            self.assertEqual([p * lam for p in a], b)

    def test_amplitude_grows_with_drop(self):
        amps = [amplitude(run_loop(0.5, 0.1, 1.0, fc, 2.0, 40000)[0]) for fc in (0.9, 0.7, 0.4)]
        self.assertLess(amps[0], amps[1])
        self.assertLess(amps[1], amps[2])


if __name__ == "__main__":
    unittest.main()
