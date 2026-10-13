"""Sweeps for robofab-selfparts. Output: experiments/results.txt (deterministic, no randomness)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from robofab_selfparts.model import Arm, gripper_parts, assemble, fractions  # noqa: E402

OUT = []


def p(*a):
    OUT.append(" ".join(str(x) for x in a))
    print(OUT[-1])


def run(arm, parts):
    done, blocked = assemble(arm, parts)
    n, m, allm = fractions(parts, done)
    return done, blocked, n, m, allm


def best_run(prt, **kw):
    """Best of the base positions in section 1's grid (ties go to the smallest base_x)."""
    bestr = None
    for i in range(0, 33):
        r = run(Arm(base_x=round(0.025 * i, 3), **kw), prt)
        if bestr is None or r[3] > bestr[3][3] + 1e-12:
            bestr = (round(0.025 * i, 3), None, None, r)
    return bestr[3], bestr[0]


parts = gripper_parts()
p("## 1. Base position sweep (default arm: opening 60 mm, push 12 N, payload 150 g)")
p("base_x_m  printed_assembled/8  printed_mass_frac  first_blockers")
best = None
for i in range(0, 33):
    bx = round(0.025 * i, 3)
    done, blocked, n, m, allm = run(Arm(base_x=bx), parts)
    why = sorted({r for k, v in blocked.items() for r in v if not r.startswith("parent")})
    p(f"{bx:.3f}  {round(n * 8)}  {m:.3f}  {'; '.join(why)}")
    if best is None or m > best[1] + 1e-12:
        best = (bx, m)
p(f"best printed-mass fraction {best[1]:.3f} first reached at base_x={best[0]:.3f}")
BX = best[0]

p()
p("## 2. Opening x push sweep, best base position per cell (printed-mass fraction assembled)")
pushes = [4, 8, 12, 16, 20, 24]
p("opening_mm  " + "  ".join(f"push{x:>2}N" for x in pushes))
for op in (20, 30, 40, 50, 60, 70):
    row = []
    for pu in pushes:
        (_, _, _, m, _), _ = best_run(parts, opening=op / 1000, push=pu)
        row.append(f"{m:7.3f}")
    p(f"{op:>9}   " + "  ".join(row))

p()
p("## 3. Screwless redesign vs original (default arm, best base position)")
for label, prt in (("original (servo screwed on)", parts), ("screwless (servo clips in)", gripper_parts(screwless=True))):
    (done, blocked, n, m, allm), bx3 = best_run(prt)
    pr = [q for q in prt if q.printed]
    p(f"{label}: assembled {len(done)}/{len(prt)} parts, printed {round(n * len(pr))}/{len(pr)}, "
      f"printed-mass frac {m:.3f}, all-mass frac {allm:.3f} (base_x={bx3:.3f}); blocked: "
      + "; ".join(f"{k}: {','.join(v)}" for k, v in blocked.items() if not v[0].startswith("parent")))

p()
p("## 4. Gripper scale sweep: can an arm with a fixed 60 mm opening make a larger or smaller gripper?")
p("scale  largest_grasp_mm  printed_mass_frac(original)  printed_mass_frac(screwless, push 16 N)")
for sc in (0.6, 0.8, 1.0, 1.2, 1.5):
    pt = gripper_parts(scale=sc)
    big = max(q.grasp for q in pt) * 1000
    (_, _, _, m1, _), _ = best_run(pt)
    (_, _, _, m2, _), _ = best_run(gripper_parts(scale=sc, screwless=True), push=16.0)
    p(f"{sc:.1f}    {big:6.1f}            {m1:.3f}                       {m2:.3f}")

p()
p("## 5. Push needed to assemble every printed part (screwless design, best base position)")
prt = gripper_parts(screwless=True)
for pu in (12, 14, 15, 16, 18):
    (done, blocked, n, m, _), bx5 = best_run(prt, push=pu)
    p(f"push {pu} N: printed {round(n * 8)}/8, printed-mass frac {m:.3f}, base_x={bx5:.3f}")

with open(os.path.join(os.path.dirname(__file__), "results.txt"), "w") as f:
    f.write("\n".join(OUT) + "\n")
