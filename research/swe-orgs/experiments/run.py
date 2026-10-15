import os, sys
H = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(H, "..", "src"))
from swe_orgs.catalogue import load, validate, tally
from swe_orgs.headroom import headroom, load_runs, wilson

rows = load(os.path.join(H, "practices.csv"))
assert not validate(rows)
print(f"catalogue: {len(rows)} practices")
for k in ("evidence", "stage", "carries_over", "status"):
    print(f"  by {k}: {tally(rows, k)}")
runs = load_runs(os.path.join(H, "..", "..", "..", "prompts", "runs.jsonl"))
print(f"\nledger headroom (prompts/runs.jsonl, {len(runs)} rows; share with the failure signal, Wilson 95%)")
for k, (a, n) in list(headroom(runs).items())[1:]:
    lo, hi = wilson(a, n)
    print(f"  {k:24s} {a:3d}/{n:3d} = {a/max(n,1):.3f}  [{lo:.3f}, {hi:.3f}]")
