import math
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from selfrep_termsat.model import Params, best_switch, dp_policy, dp_solve, value

P = Params(k=0.1, c=math.inf, horizon=40.0, dt=0.5)


class TermSat(unittest.TestCase):
    def test_zero_terminal_matches_satmarket_dp(self):
        from selfrep_satmarket.model import dp_solve as base
        v0, _, _ = dp_solve(P, 0.0, n_points=100)
        self.assertAlmostEqual(v0, base(P, n_points=100)[0], places=9)

    def test_large_terminal_value_never_switches(self):
        _, pol, grid = dp_solve(P, 50.0, n_points=100)   # s >> a/k = 10
        j, n, path = value(P, dp_policy(P, pol, grid), 50.0)
        self.assertTrue(all(u > 0.95 for u in path[:-2]))  # last step touches the grid edge

    def test_dp_not_worse_than_bang_bang(self):
        for s in (0.0, 4.0):
            _, pol, grid = dp_solve(P, s, n_points=200)
            jd = value(P, dp_policy(P, pol, grid), s)[0]
            self.assertGreaterEqual(jd, best_switch(P, s)[1] * 0.995)

    def test_terminal_value_raises_objective(self):
        self.assertGreater(best_switch(P, 4.0)[1], best_switch(P, 0.0)[1])


if __name__ == "__main__":
    unittest.main()
