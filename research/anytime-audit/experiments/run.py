import os, sys, math, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from anytime_audit import *

out = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s); out.append(s)
a, delta, N = 0.05, 0.05, 1000
p(f"Setup: honest step flags w.p. a={a} (float drift), corrupted step w.p. p; level delta={delta}; horizon N={N}")

p("E1. type-I error of an honest prover (p=a), 3000 runs: peeking slashes honest provers")
rng = random.Random(0)
for name, fn in (("fixed-n test at n=N", None), ("peeking every audit", lambda g: run_peeking(g, a, a, delta, N)),
                 ("peeking every 50", lambda g: run_peeking(g, a, a, delta, N, 50)), ("mixture e-process", lambda g: run_mixture(g, a, a, delta, N))):
    if fn is None:
        thr = fixed_n_threshold(N, a, delta); r = sum(sum(rng.random() < a for _ in range(N)) >= thr for _ in range(3000)) / 3000
    else: r, _ = rate(rng, fn, 3000)
    p(f"  {name:22s} false-slash rate {r:.3f}")

p("E2. expected audits to slash a corrupted prover (delta=0.05, 2000 runs); ideal = ln(1/delta)/KL(p||a)")
for pt in (0.10, 0.20, 0.40):
    ideal = math.log(1 / delta) / kl_bern(pt, a)
    nfix = fixed_n_needed(a, pt, delta, 0.8)
    rs, ms = rate(rng, lambda g: run_sprt(g, a, pt, pt, delta, 5000), 2000)
    rm, mm = rate(rng, lambda g: run_mixture(g, a, pt, delta, 5000), 2000)
    p(f"  p={pt:.2f}: ideal {ideal:6.1f} | SPRT(knows p) {ms:6.1f} | mixture {mm:6.1f} (detect {rm:.3f}) | fixed-n for 80% power n={nfix}")

p("E3. mis-planned fixed test: planned for p=0.4 (n from E2), true p=0.15; SPRT tuned to 0.4; mixture adapts")
n_plan = fixed_n_needed(a, 0.40, delta, 0.8); thr = fixed_n_threshold(n_plan, a, delta); pt = 0.15
pw = binom_sf(thr, n_plan, pt)
rs, ms = rate(rng, lambda g: run_sprt(g, a, pt, 0.40, delta, 5000), 1500)
rm, mm = rate(rng, lambda g: run_mixture(g, a, pt, delta, 5000), 1500)
p(f"  fixed n={n_plan}: power {pw:.3f} | SPRT(0.4) detect-by-5000 {rs:.3f} mean {ms:.0f} | mixture detect {rm:.3f} mean {mm:.0f} (ideal {math.log(1/delta)/kl_bern(pt,a):.0f})")

p("E4. cost of not knowing p: mixture / ideal expected audits, by delta (p=0.2)")
for d in (0.05, 0.01, 0.001):
    ideal = math.log(1 / d) / kl_bern(0.2, a)
    _, mm = rate(rng, lambda g: run_mixture(g, a, 0.2, d, 5000), 1500)
    p(f"  delta={d}: ideal {ideal:.1f} mixture {mm:.1f} ratio {mm/ideal:.2f}")
open(os.path.join(os.path.dirname(__file__), "results.txt"), "w").write("\n".join(out) + "\n")
