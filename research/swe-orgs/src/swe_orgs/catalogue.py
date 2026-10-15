"""Load, validate and summarise the practice catalogue (pure Python)."""
import csv

FIELDS = ["id", "practice", "source", "year", "company", "stage", "evidence", "claims_to_improve",
          "loop_mapping", "carries_over", "headroom_metric", "status"]
EVIDENCE = {"measured", "case-study", "opinion"}
STAGES = {"early", "growth", "large"}
CARRIES = {"yes", "partly", "no"}
STATUS = {"candidate", "not-proposed", "already-in-loop"}


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validate(rows):
    """Return a list of problems; empty means the catalogue is well formed."""
    errs, seen = [], set()
    for i, r in enumerate(rows, 2):
        if list(r.keys()) != FIELDS:
            errs.append(f"row {i}: columns differ from FIELDS")
            continue
        if r["id"] in seen:
            errs.append(f"row {i}: duplicate id {r['id']}")
        seen.add(r["id"])
        for k in FIELDS:
            if not (r[k] or "").strip():
                errs.append(f"row {i}: empty {k}")
        if r["evidence"] not in EVIDENCE:
            errs.append(f"row {i}: bad evidence {r['evidence']!r}")
        if r["stage"] not in STAGES:
            errs.append(f"row {i}: bad stage {r['stage']!r}")
        if r["carries_over"] not in CARRIES:
            errs.append(f"row {i}: bad carries_over {r['carries_over']!r}")
        if r["status"] not in STATUS:
            errs.append(f"row {i}: bad status {r['status']!r}")
        if not r["year"].isdigit() or not 1990 <= int(r["year"]) <= 2026:
            errs.append(f"row {i}: bad year {r['year']!r}")
    return errs


def tally(rows, key):
    out = {}
    for r in rows:
        out[r[key]] = out.get(r[key], 0) + 1
    return dict(sorted(out.items()))
