"""Cross-fitted DR pseudo-labels and validation-chosen caps. Writes experiments/results.txt."""
import numpy as np

from ambient_crossfit.core import FIT_NAMES, INFORMED_W, PRIOR_W, World, oracle_weights, run_fixed, run_logged, simulate

SEEDS = 20
H = 100
EPS = [0.002, 0.005, 0.02]
PRIORS = {"uninformed": PRIOR_W, "informed": INFORMED_W}
out = []


def log(s=""):
    print(s); out.append(s)


def ms(x):
    return f"{np.mean(x):6.2f} +- {np.std(x):5.2f}"


wd = World()
wo = oracle_weights(wd, np.random.default_rng(12345), 2000)
held = [simulate(wd, 100, np.random.default_rng(5000 + s)) for s in range(SEEDS)]
oracle_held = np.mean([run_fixed(wd, h, wo).sum() / 100 for h in held])
log(f"oracle utility/h on held-out {oracle_held:.2f}")
log(f"{SEEDS} seeds, fits at hour {H}; scored on fresh 100 h held-out streams, no exploration; '+-' is std over seeds")
log(f"{'prior':11s} {'eps':>6s} {'fit':>16s} {'utility/h':>15s}   chosen caps (outcome=clip10-cf | outcome=prior), counts")
for pname, pw in PRIORS.items():
    for eps in EPS:
        res = {k: [] for k in FIT_NAMES}; caps1, caps2 = [], []
        for s in range(SEEDS):
            d = simulate(wd, H, np.random.default_rng(1000 + s))
            fits, info = run_logged(wd, d, np.random.default_rng(s), eps=eps, prior_w=pw, hours=(H,))
            caps1.append(info[H]["cap"]); caps2.append(info[H]["cap_prior"])
            for k in FIT_NAMES:
                res[k].append(run_fixed(wd, held[s], fits[H][k]).sum() / 100)
        cnt = lambda c: {str(x): c.count(x) for x in sorted(set(c))}
        for k in FIT_NAMES:
            extra = f"   {cnt(caps1)} | {cnt(caps2)}" if k == "dr_cf_sel" else ""
            log(f"{pname:11s} {eps:6.3f} {k:>16s} {ms(res[k]):>15s}{extra}")
open("experiments/results.txt", "w").write("\n".join(out) + "\n")
