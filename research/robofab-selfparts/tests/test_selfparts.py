import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from robofab_selfparts.model import Arm, ik_2r, reachable, gripper_parts, assemble, fractions, step_check  # noqa: E402


class TestKinematics(unittest.TestCase):
    def test_ik_roundtrip(self):
        import math
        a = Arm()
        for x, z in [(0.2, 0.1), (-0.1, 0.25), (0.3, -0.05)]:
            for q1, q2 in ik_2r(a, x, z):
                q1, q2 = math.radians(q1), math.radians(q2)
                fx = a.l1 * math.cos(q1) + a.l2 * math.cos(q1 + q2)
                fz = a.l1 * math.sin(q1) + a.l2 * math.sin(q1 + q2)
                self.assertAlmostEqual(fx, x, 9)
                self.assertAlmostEqual(fz, z, 9)

    def test_out_of_reach(self):
        self.assertEqual(ik_2r(Arm(), 0.5, 0.0), [])

    def test_dead_zone_under_base(self):
        # directly below the base needs a folded elbow beyond its limit
        a = Arm(base_x=0.4)
        self.assertFalse(reachable(a, 0.4, 0.02, -90))
        self.assertTrue(reachable(Arm(base_x=0.025), 0.30, 0.0, -90))


class TestAssembly(unittest.TestCase):
    def test_narrow_opening_blocks_root(self):
        done, blocked = assemble(Arm(base_x=0.025, opening=0.040), gripper_parts())
        self.assertEqual(done, [])
        self.assertIn("grasp wider than opening", blocked["palm"])

    def test_screw_needs_driver(self):
        a = Arm(base_x=0.025)
        servo = [p for p in gripper_parts() if p.name == "servo"][0]
        self.assertIn("needs a screwdriver", step_check(a, servo))

    def test_children_wait_for_parent(self):
        done, _ = assemble(Arm(base_x=0.025), gripper_parts())
        order = {n: i for i, n in enumerate(done)}
        for p in gripper_parts():
            if p.name in order and p.parent:
                self.assertLess(order[p.parent], order[p.name])

    def test_push_unlocks_all_printed(self):
        prt = gripper_parts(screwless=True)
        _, _, n, m, _ = (None, None) + fractions(prt, assemble(Arm(base_x=0.05, push=16.0), prt)[0])
        self.assertEqual(n, 1.0)
        self.assertAlmostEqual(m, 1.0)

    def test_more_push_never_hurts(self):
        prt = gripper_parts(screwless=True)
        last = -1.0
        for push in range(4, 26, 2):
            m = fractions(prt, assemble(Arm(base_x=0.05, push=float(push)), prt)[0])[1]
            self.assertGreaterEqual(m, last)
            last = m

    def test_partition(self):
        prt = gripper_parts()
        done, blocked = assemble(Arm(base_x=0.025), prt)
        self.assertEqual(set(done) | set(blocked), {p.name for p in prt})
        self.assertFalse(set(done) & set(blocked))


if __name__ == "__main__":
    unittest.main()
