import math, random, unittest
from loop_closure_twin.model import *

BASE = Chain(40, 1e-4, 1e-6, 1e-4)


class TestLoopClosureTwin(unittest.TestCase):
    def test_closed_form_matches_monte_carlo(self):
        rng = random.Random(1)
        g = gain_twin(BASE, BASE.sig2)
        for k in (10, 25):
            self.assertAlmostEqual(simulate(BASE, g, k, 40000, rng) / real_var(BASE, g, k), 1.0, delta=0.04)

    def test_twin_world_is_self_consistent(self):
        ch = BASE.replace(q=0.0)
        for k in (1, 20, 40):
            self.assertAlmostEqual(real_var(ch, gain_twin(ch, ch.sig2), k), claimed_var(ch, ch.sig2, k), places=12)

    def test_per_pose_optimum_beats_any_linear_gain(self):
        for k in (5, 20, 40):
            for g in (gain_twin(BASE, BASE.sig2), gain_end(BASE), 0.0, 1.0 / 40):
                self.assertLessEqual(profile_opt(BASE, k) - 1e-15, real_var(BASE, g, k))

    def test_drift_makes_twin_overconfident(self):
        r = [nees_ratio(BASE.replace(q=q), BASE.sig2, 20) for q in (1e-7, 1e-6, 1e-5)]
        self.assertTrue(1.0 < r[0] < r[1] < r[2])

    def test_certified_length_is_too_long_under_drift(self):
        base = BASE.replace(q=1e-6)
        tau2 = 1.6e-3
        nt = max_length_claimed(base, base.sig2, tau2)
        self.assertGreater(nt, max_length_real(base, tau2, lambda c: gain_twin(c, base.sig2)))

    def test_audit_power_rises_with_samples_and_size_is_nominal(self):
        rng = random.Random(2)
        self.assertAlmostEqual(nees_power(1.0, 10, rng, draws=6000)[0], 0.05, delta=0.015)
        self.assertLess(nees_power(2.2, 3, rng, draws=4000)[0], nees_power(2.2, 30, rng, draws=4000)[0])
