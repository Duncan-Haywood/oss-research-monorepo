"""How much can a quality practice gain? Upper bound from the run ledger."""
import json, math


def wilson(k, n, z=1.959964):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def load_runs(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def headroom(runs):
    """Counts of the failure signals a review/CI/release practice could remove."""
    n = len(runs)
    partial = sum(1 for r in runs if r.get("outcome") != "success")
    ci_known = [r for r in runs if r.get("ci_failures_before_green") is not None]
    ci_bad = sum(1 for r in ci_known if r["ci_failures_before_green"] > 0)
    rv_known = [r for r in runs if r.get("review_findings") is not None]
    rv_bad = sum(1 for r in rv_known if r["review_findings"] > 0)
    integ = sum(1 for r in runs if r.get("integrity_issues"))
    collide = sum(1 for r in runs if any("collision" in e or "concurrent" in e
                                          for e in (r.get("errors") or [])))
    return {"runs": n, "not_success": (partial, n), "ci_failed_before_green": (ci_bad, len(ci_known)),
            "review_findings": (rv_bad, len(rv_known)), "integrity_run": (integ, n),
            "parallel_collision": (collide, n)}
