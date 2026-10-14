"""Gated-textile bounds (tau .15 closed, .8 open) under 'ours' and 'ref' design choices, after 3 h and at
steady state (1440 min). Deterministic; writes experiments/results.txt."""
import os, sys, warnings
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from garment_twonodegate import gate
warnings.filterwarnings("ignore")
out = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); out.append(s)

ROOMS = (31, 16)
CH = {"ours": gate.OURS, "ref": gate.REF}
P("== A. end states, 1.2 met, 0.5 clo, 50% rh, v 0.1, air = radiant temperature. Columns: tsk C, tcr C, wettedness, dry W/m2, evap W/m2 ==")
res = {}
for room in ROOMS:
    for nm, o in CH.items():
        for tag, m in (("3h", gate.HOURS3), ("ss", gate.STEADY)):
            res[room, nm, tag] = gate.bounds(room, o, m)
            for lab, r in zip(("closed .15", "open .8  "), res[room, nm, tag]):
                P(f"{room} C {nm:4s} {tag:2s} {lab}: {r['tsk']:.2f} {r['tcr']:.2f} {r['wet']:.2f} {r['dry']:7.1f} {r['evap']:6.1f}")

P("\n== B. open minus closed (the value of opening the gate) ==")
for room in ROOMS:
    for nm in CH:
        for tag in ("3h", "ss"):
            c, o = res[room, nm, tag]
            P(f"{room} C {nm:4s} {tag:2s}: dTsk {o['tsk']-c['tsk']:+.2f} C  dTcr {o['tcr']-c['tcr']:+.2f} C  dWet {o['wet']-c['wet']:+.3f}  dDry {o['dry']-c['dry']:+.1f}  dEvap {o['evap']-c['evap']:+.1f} W/m2")

P("\n== C. steady state reached? max change tsk/tcr/dry/evap between 1440 and 2880 min ==")
worst = 0.0
for room in ROOMS:
    for nm, o in CH.items():
        for a, b in zip(res[room, nm, "ss"], gate.bounds(room, o, 2880)):
            worst = max(worst, max(abs(a[k] - b[k]) for k in ("tsk", "tcr", "dry", "evap")))
P(f"worst change: {worst:.4f}")
open(os.path.join(os.path.dirname(__file__), "results.txt"), "w").write("\n".join(out) + "\n")
