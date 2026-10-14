import math, pathlib, sys
here = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(here / "src"))
sys.path.insert(0, str(here.parent / "selfrep-growth" / "src"))
from selfrep_growth.params import printer_copy
from selfrep_termsat.model import Params, best_switch, dp_policy, dp_solve, value

W, V, _, _ = printer_copy()
T = 600.0
k = 1 / W
out = [f"assumed inputs: a=1 per machine-hour; W={W:.1f} h per copy (selfrep-growth); k=1/W={k:.4f}/h (no failures); T={T:.0f} h; fleet starts at 1",
       "fluid model, cash free, Euler step 1 h; objective = revenue a c (1-exp(-g/c)) + s x (machines at T); s is a fraction of a/k (assumed)",
       "J values are Euler values; percentages are of the DP policy's simulated J", ""]
for c in (math.inf, 1e4, 1e3, 1e2):
    p = Params(k=k, c=c, horizon=T)
    out.append(f"== c={'inf' if math.isinf(c) else f'{c:g}'}")
    for frac in (0.0, 0.25, 0.5, 1.0, 1.5):
        s = frac / k
        vdp, pol, grid = dp_solve(p, s)
        pol_fn = dp_policy(p, pol, grid)
        jd, nd, path = value(p, pol_fn, s)
        ts, jb, nb = best_switch(p, s)
        half = next((i for i, u in enumerate(path) if u < 0.5), len(path))
        mid = sum(1 for u in path if 0.02 < u < 0.98)
        out.append(f"s={s:6.1f} ({frac:4.2f} a/k): DP J={jd:12.1f} N_T={nd:9.1f} u<0.5 from t={half:3d} ({mid:3d} h interior) | "
                   f"bang-bang ts={ts:4.0f} {100*jb/jd:6.2f}% | DP table vs policy {100*(vdp-jd)/jd:+.2f}%")
    out.append("")
pathlib.Path(here / "experiments" / "results.txt").write_text("\n".join(out) + "\n")
print("\n".join(out))
