import math
import unittest

from backlash_twin.model import (simulate, simulate_twin, measure, twin_amplitude, twin_rms_error, cycle_candidates,
                                 cycle_error_rms, stuck_possible, step)

K, D, P = 0.5, 0.1, 10


class T(unittest.TestCase):
    def test_twin_closed_forms(self):
        for A in (0.05, 1.0):
            sw, er = measure(simulate_twin(K, P, A), P)
            self.assertAlmostEqual(sw, twin_amplitude(K, P, A), places=9)
            self.assertAlmostEqual(er, twin_rms_error(K, P, A), places=9)

    def test_load_rests_inside_play_and_follows_at_contact(self):
        x, g = step(1.0, 0.0, 0.5, 0.1, 0.0)      # motor moves -0.5, gap -0.5 < -d: load pushed to x + (g+d)
        self.assertAlmostEqual(g, -0.1)
        self.assertAlmostEqual(x, 0.6)
        x, g = step(0.0, 0.0, 0.5, 0.1, 0.1)      # motor moves +0.05, inside play: load does not move
        self.assertEqual(x, 0.0)
        self.assertAlmostEqual(g, 0.05)

    def test_moving_cycle_matches_simulation_when_unique(self):
        for A in (0.085, 0.1, 0.2, 0.5, 1.0):
            (n, a), = cycle_candidates(K, D, P, A)
            sw, er = measure(simulate(K, D, P, A), P)
            self.assertAlmostEqual(sw, a, places=9)
            self.assertAlmostEqual(er, cycle_error_rms(K, D, P, A, n, a), places=9)

    def test_stuck_iff_excursion_fits_and_error_is_half_amplitude(self):
        for A in (0.03, 0.05):
            self.assertTrue(stuck_possible(K, D, P, A))
            sw, er = measure(simulate(K, D, P, A, g0=-D), P)
            self.assertEqual(sw, 0.0)
            self.assertAlmostEqual(er, A / 2, places=12)
        self.assertFalse(stuck_possible(K, D, P, 0.085))
        self.assertEqual(cycle_candidates(K, D, P, 0.05), [])

    def test_bistability_between_stuck_and_moving(self):
        A = 0.07
        self.assertTrue(stuck_possible(K, D, P, A))
        (n1, a1), (n2, a2) = cycle_candidates(K, D, P, A)
        self.assertEqual(measure(simulate(K, D, P, A, g0=-D), P)[0], 0.0)
        self.assertAlmostEqual(measure(simulate(K, D, P, A, g0=0.0), P)[0], a1, places=9)

    def test_real_worse_than_twin_at_small_amplitude_but_close_at_large(self):
        r = lambda A: measure(simulate(K, D, P, A), P)[1] / twin_rms_error(K, P, A)
        self.assertGreater(r(0.1), 1.9)
        self.assertLess(r(1.0), 1.12)


if __name__ == "__main__":
    unittest.main()
