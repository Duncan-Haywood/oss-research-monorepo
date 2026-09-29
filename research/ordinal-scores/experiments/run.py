import math, random
from ordinal_scores import *

K = 10
print("E1 shift mass eps from bin 0 to bin d (K=10): regret/eps^2 and per unit payment range (Brier 2, RPS K-1=9)")
p = uniform(K)
for d in (1, 2, 5, 9):
    r = shift(p, 0, d, 1e-3)
    a, b = rps_regret(r, p) / 1e-6, brier_regret(r, p) / 1e-6
    print(f" d={d}  rps {a:5.2f} ({a/(K-1):.3f}/range)  brier {b:5.2f} ({b/2:.3f}/range)  rps/brier per range {(a/(K-1))/(b/2):.3f} = d/(K-1)")

print("\nE2 worst-case regret (exact vertex), K=10")
bell = [math.exp(-(j - 4.5) ** 2 / 4) for j in range(K)]
bell = [x / sum(bell) for x in bell]
edge = [.001] * (K - 1) + [1 - .001 * (K - 1)]
for name, q in (("uniform", uniform(K)), ("bell", bell), ("mass at top", edge)):
    print(f" {name:12s} rps max {max_regret_rps(q):.3f} (range {K-1})  brier max {max_regret_brier(q):.3f} (range 2)")

print("\nE3 misreport = truth translated by s bins (narrow truth on bins 4,5): regret")
q = [0] * K
q[4] = q[5] = .5
for s in (1, 2, 3, 4):
    r = [0.0] * K
    for j, x in enumerate(q):
        r[min(K - 1, j + s)] += x
    print(f" s={s}  rps {rps_regret(r,q):6.3f}  brier {brier_regret(r,q):6.3f}")

print("\nE4 neighbour-blur misreport of a bell truth (K=10)")
for a in (.05, .1, .25):
    r = blur(bell, a)
    kl = sum(x * math.log(x / y) for x, y in zip(bell, r))
    print(f" a={a:<5g} rps {rps_regret(r,bell):.5f}  brier {brier_regret(r,bell):.5f}  kl {kl:.5f}")

print("\nE5 tolerance pricing: weight only threshold t, decision regret <= 2*sqrt(excess weighted RPS); 20000 random pairs")
rng = random.Random(0)
worst, hit = 0.0, 0
for _ in range(20000):
    k = rng.randint(3, 8)
    pv = [rng.random() ** 3 + 1e-3 for _ in range(k)]; pv = [x / sum(pv) for x in pv]
    rv = [rng.random() ** 3 + 1e-3 for _ in range(k)]; rv = [x / sum(rv) for x in rv]
    t = rng.randrange(k - 1)
    w = [0.0] * (k - 1); w[t] = 1.0
    dr = decision_regret(rv, pv, t)
    if dr > 0:
        hit += 1
        worst = max(worst, dr / (2 * math.sqrt(rps_regret(rv, pv, w))))
print(f" wrong-decision cases {hit}, max regret/bound {worst:.3f} (<=1)")
