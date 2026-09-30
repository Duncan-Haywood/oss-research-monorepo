import math, random, unittest
from sync_twin import *

SIG = 0.2


class M(unittest.TestCase):
    def test_twin_recall_is_nominal_without_jitter(self):
        g = design_gate(SIG, 0.99)
        self.assertAlmostEqual(recall_jitter(g, SIG, 10, 0.0), 0.99, places=12)
        self.assertAlmostEqual(recall_jitter(g, SIG, 0, 0.05), 0.99, places=12)   # stationary target: blind to jitter

    def test_recall_matches_simulation(self):
        rng = random.Random(1)
        v, s = 10.0, 0.02
        g = design_gate(SIG, 0.99)
        n = 200000
        hit = sum(abs(b - a) < g for a, b in sim_diffs(rng, SIG, v, s, n)) / n
        self.assertAlmostEqual(hit, recall_jitter(g, SIG, v, s), delta=0.003)

    def test_speed_inverts_recall(self):
        g = design_gate(SIG, 0.99)
        v = speed_at_recall(g, SIG, 0.02, 0.90)
        self.assertAlmostEqual(recall_jitter(g, SIG, v, 0.02), 0.90, places=10)

    def test_repair_restores_recall_and_scales_by_sqrt_kappa(self):
        v, s = 12.0, 0.02
        g2 = gate_repair(SIG, v, s, 0.99)
        self.assertAlmostEqual(recall_jitter(g2, SIG, v, s), 0.99, places=12)
        self.assertAlmostEqual(g2 / design_gate(SIG, 0.99), math.sqrt(kappa(SIG, v, s)), places=12)

    def test_bias_recall_below_jitter_at_equal_rms_shift(self):
        g = design_gate(SIG, 0.99)
        self.assertLess(recall_bias(g, SIG, 10, 0.02), 0.99)
        self.assertAlmostEqual(recall_bias(g, SIG, 10, 0.0), 0.99, places=12)

    def test_fused_mse_matches_simulation_and_kappa(self):
        rng = random.Random(2)
        v, s = 10.0, 0.03
        self.assertAlmostEqual(fused_mse(SIG, v, s, 0.5), kappa(SIG, v, s) * SIG ** 2 / 2, places=12)
        for w in (0.5, w_opt(SIG, v, s)):
            sim = sim_fused_mse(rng, SIG, v, s, w, 300000)
            self.assertAlmostEqual(sim / fused_mse(SIG, v, s, w), 1.0, delta=0.015)

    def test_optimal_weight_minimises(self):
        v, s = 10.0, 0.03
        w = w_opt(SIG, v, s)
        self.assertAlmostEqual(fused_mse(SIG, v, s, w), mse_opt(SIG, v, s), places=12)
        for dw in (-0.05, 0.05):
            self.assertGreater(fused_mse(SIG, v, s, w + dw), mse_opt(SIG, v, s))

    def test_equal_weight_beats_single_sensor_iff_kappa_below_2(self):
        self.assertLess(fused_mse(SIG, 5, 0.02, 0.5), SIG ** 2)      # v s = 0.1 < sqrt2 sigma
        self.assertGreater(fused_mse(SIG, 20, 0.02, 0.5), SIG ** 2)  # v s = 0.4 > sqrt2 sigma

    def test_neighbour_confusion_rises_with_wider_gate(self):
        a = neighbour_assoc(design_gate(SIG, 0.99), 1.0, SIG, 10, 0.02)
        b = neighbour_assoc(gate_repair(SIG, 10, 0.02, 0.99), 1.0, SIG, 10, 0.02)
        self.assertGreater(b, a)


if __name__ == "__main__":
    unittest.main()
