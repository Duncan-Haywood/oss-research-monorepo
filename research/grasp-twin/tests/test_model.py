import math, unittest
from grasp_twin import *

L = load(0.5, 3.0)
MU0, S, CD, CF = 0.5, 0.35, 1.0, 0.01
N0 = L / (2 * MU0)


class T(unittest.TestCase):
    def test_closed_form_optimum_matches_grid(self):
        z = z_star(N0, S, CD, CF)
        zb, jb = brute_force_z(N0, S, CD, CF, n=8000)
        self.assertAlmostEqual(z, zb, delta=0.005)
        self.assertAlmostEqual(best_force(L, MU0, S, CD, CF)[1], jb, places=6)

    def test_static_threshold_and_dynamic_sim(self):
        m, a = 0.5, 3.0
        N_thr = L / (2 * 0.6)
        self.assertFalse(simulate_grasp(N_thr * 1.01, 0.6, m, a))
        self.assertTrue(simulate_grasp(N_thr * 0.99, 0.6, m, a))

    def test_drop_probability_matches_dynamic_simulation(self):
        N = best_force(L, MU0, S, CD, CF)[0]
        sim = simulate_drop_rate(N, 0.5, 3.0, MU0, S, 6000, seed=3)
        self.assertAlmostEqual(sim, real_drop(N, L, MU0, S), delta=0.008)

    def test_deterministic_twin_grips_at_its_own_threshold(self):
        for b in (-0.3, 0.0, 0.4):
            mu_t = MU0 * math.exp(b)
            N = twin_force(L, mu_t, 0.0, CD, CF)
            self.assertAlmostEqual(N, L / (2 * mu_t), places=12)
            self.assertAlmostEqual(real_drop(N, L, MU0, S), Phi(b / S), places=12)
        self.assertAlmostEqual(real_drop(twin_force(L, MU0, 0.0, CD, CF), L, MU0, S), 0.5, places=12)
        mean = MU0 * math.exp(S * S / 2)
        self.assertAlmostEqual(real_drop(twin_force(L, mean, 0.0, CD, CF), L, MU0, S), Phi(S / 2), places=12)

    def test_randomised_twin_real_drop_law(self):
        b, st = 0.3, 0.25
        mu_t = MU0 * math.exp(b)
        Nt = twin_force(L, mu_t, st, CD, CF)
        z = z_star(L / (2 * mu_t), st, CD, CF)
        self.assertAlmostEqual(real_drop(Nt, L, MU0, S), Phi((b + st * z) / S), places=12)

    def test_matched_twin_has_zero_regret_and_others_positive(self):
        self.assertAlmostEqual(regret(L, MU0, S, CD, CF, MU0, S), 0.0, places=12)
        for mu_t, st in ((MU0 * 1.5, S), (MU0, 0.0), (MU0, 0.1), (MU0 * 0.7, 0.5)):
            self.assertGreater(regret(L, MU0, S, CD, CF, mu_t, st), 0.0)

    def test_predictive_drop_exact_vs_monte_carlo_and_multiplier(self):
        k = Phi_inv(0.01)
        self.assertAlmostEqual(predictive_drop(10, k), sample_plugin_drop(10, k, 60000, 4), delta=0.0012)
        self.assertGreater(predictive_drop(10, k), 0.01)
        kn = plugin_multiplier(10, 0.01)
        self.assertLess(kn, k)
        self.assertAlmostEqual(predictive_drop(10, kn), 0.01, places=6)
        self.assertAlmostEqual(predictive_drop(2000, k), 0.01, delta=0.0002)


if __name__ == "__main__":
    unittest.main()
