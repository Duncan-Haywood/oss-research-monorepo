"""Run: PYTHONPATH=src python3 experiments/run.py > experiments/results.txt  (also writes experiments/dscorr.png)"""
import numpy as np
from ambient_dscorr.sim import Params, contexts
from ambient_dscorr.est import (PRIOR, confusion, joint_audit2c, draw_audit2c, estimate_naive, estimate_em,
                                estimate_ds, u_table, policies)

P = Params()
CTX = contexts()
U = [u_table(P, c) for c in CTX]
REPS = 200
ALPHA = 1.0
RHOS = (0.0, 0.25, 0.5, 0.75)
NS = (200, 1000)


def val(C, pe, Ce):
    v = [policies(u, C, PRIOR, pe, Ce, pe, Ce) for u in U]
    return {k: float(np.mean([x[k] for x in v])) for k in ("blind", "bayes_true", "bayes_naive")}


def v_of(C, pe, Ce):
    return val(C, pe, Ce)["bayes_naive"]          # 'bayes_naive' slot = the supplied estimate


print(f"Mean utility per message over {len(CTX)} contexts; uniform-error label and auditors; true mix 0.5/0.35/0.15; {REPS} audit sets per finite cell")
print("Shared-error model: with probability rho a message's auditor-2 label is a copy of auditor-1's; else independent.")
print("Both auditors have the same accuracy, so each one's own accuracy is unchanged by rho.\n'naive' = auditor 1 as truth; 'em-known' = EM with auditor 1's true matrix, one label per message;")
print("'ds' = Dawid-Skene assuming independent auditors, no matrix known. 'acc-hat' = mean diagonal of the fitted matrix.\n")

res = {}
for la in (0.7, 0.9):
    C = confusion(la)
    base = val(C, PRIOR, C)
    for (a1, a2) in ((0.8, 0.8), (0.7, 0.7)):
        A1, A2 = confusion(a1), confusion(a2)
        print(f"-- label accuracy {la}, auditors {a1}/{a2}: true-param Bayes {base['bayes_true']:.4f}, blind {base['blind']:.4f}")
        print("   POPULATION  rho  naive    em-known  ds       ds acc-hat: label  aud1   aud2")
        for rho in RHOS:
            J = joint_audit2c(C, A1, A2, PRIOR, rho) * 1e9
            pn, Cn = estimate_naive(J.sum(axis=1), 0.0)
            pk, Ck = estimate_em(J.sum(axis=1), A1, iters=5000)
            pd, Cd, h1, h2 = estimate_ds(J, iters=20000)
            r = (v_of(C, pn, Cn), v_of(C, pk, Ck), v_of(C, pd, Cd))
            res[(la, a1, rho, "pop")] = r
            print(f"               {rho:4.2f}  {r[0]:.4f}   {r[1]:.4f}   {r[2]:.4f}          {np.diag(Cd).mean():.3f}  {np.diag(h1).mean():.3f}  {np.diag(h2).mean():.3f}")
        for n in NS:
            print(f"   n={n}        rho  naive    em-known  ds       std(ds)  P(ds<blind)  ds acc-hat label")
            for rho in RHOS:
                rng = np.random.default_rng(int(1e5 * la) + int(1e3 * a1) + int(100 * rho) + n)
                rows, accs = [], []
                for _ in range(REPS):
                    c2 = draw_audit2c(C, A1, A2, PRIOR, n, rho, rng)
                    pn, Cn = estimate_naive(c2.sum(axis=1), ALPHA)
                    pk, Ck = estimate_em(c2.sum(axis=1), A1)
                    pd, Cd, _, _ = estimate_ds(c2, iters=2000, tol=1e-10)
                    rows.append([v_of(C, pn, Cn), v_of(C, pk, Ck), v_of(C, pd, Cd)])
                    accs.append(np.diag(Cd).mean())
                r = np.array(rows)
                res[(la, a1, rho, n)] = r.mean(axis=0)
                print(f"               {rho:4.2f}  {r[:,0].mean():.4f}   {r[:,1].mean():.4f}   {r[:,2].mean():.4f}   {r[:,2].std():.4f}    {np.mean(r[:,2]<base['blind']-1e-12):.2f}         {np.mean(accs):.3f}")
        print()

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.4))
    for k, (la, a1) in enumerate(((0.7, 0.8), (0.9, 0.8))):
        base = val(confusion(la), PRIOR, confusion(la))
        axs[k].plot(RHOS, [res[(la, a1, r, "pop")][2] for r in RHOS], "o-", color="C0", label="ds, population")
        axs[k].plot(RHOS, [res[(la, a1, r, "pop")][0] for r in RHOS], "x--", color="C1", label="naive, population")
        axs[k].plot(RHOS, [res[(la, a1, r, "pop")][1] for r in RHOS], "s:", color="C2", label="em-known (oracle)")
        axs[k].axhline(base["bayes_true"], color="k", ls=":", lw=1, label="true-parameter Bayes")
        axs[k].axhline(base["blind"], color="gray", ls="-", lw=1, label="blind")
        axs[k].set_xlabel("shared-error probability rho"); axs[k].set_ylabel("mean utility per message")
        axs[k].set_title(f"label acc {la}, auditors {a1}/{a1}", fontsize=9); axs[k].legend(fontsize=6)
    fig.suptitle("Stylised model: Dawid-Skene when auditors share errors", fontsize=9)
    fig.tight_layout(); fig.savefig("experiments/dscorr.png", dpi=110)
except ImportError:
    pass
