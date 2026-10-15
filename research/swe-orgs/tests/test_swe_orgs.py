import os, sys, unittest
H = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(H, "..", "src"))
from swe_orgs.catalogue import load, validate, tally, FIELDS
from swe_orgs.headroom import wilson, headroom

CSV = os.path.join(H, "..", "experiments", "practices.csv")


class T(unittest.TestCase):
    def test_catalogue_valid(self):
        rows = load(CSV)
        self.assertGreaterEqual(len(rows), 7)
        self.assertEqual(validate(rows), [])

    def test_validate_catches_problems(self):
        row = {k: "x" for k in FIELDS}
        row.update(id="a", evidence="rumour", year="1800")
        errs = validate([row, dict(row)])
        self.assertTrue(any("duplicate" in e for e in errs))
        self.assertTrue(any("evidence" in e for e in errs))
        self.assertTrue(any("year" in e for e in errs))

    def test_sources_are_cited_with_a_url_or_doi(self):
        for r in load(CSV):
            self.assertRegex(r["source"], r"https?://")

    def test_tally(self):
        self.assertEqual(sum(tally(load(CSV), "evidence").values()), len(load(CSV)))

    def test_wilson(self):
        lo, hi = wilson(0, 100)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.0370, places=3)
        self.assertEqual(wilson(0, 0), (0.0, 1.0))

    def test_headroom_counts(self):
        runs = [{"outcome": "success", "ci_failures_before_green": 0, "review_findings": 0},
                {"outcome": "partial", "ci_failures_before_green": 2, "review_findings": None,
                 "errors": ["slug collision"]},
                {"outcome": "success", "integrity_issues": ["x"]}]
        h = headroom(runs)
        self.assertEqual(h["not_success"], (1, 3))
        self.assertEqual(h["ci_failed_before_green"], (1, 2))
        self.assertEqual(h["review_findings"], (0, 1))
        self.assertEqual(h["integrity_run"], (1, 3))
        self.assertEqual(h["parallel_collision"], (1, 3))


if __name__ == "__main__":
    unittest.main()
