"""Loop closure tuned in a digital twin. Base case (chosen, not measured): n=40 steps, per-step odometry sd 1 cm (sig2=1e-4),
loop-closure sd 1 cm (sc2=1e-4); real bias random walk with per-step variance q (twin: q=0)."""
import math, os, random, statistics, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from loop_closure_twin.model import *

BASE = Chain(40, 1e-4, 0.0, 1e-4)
ST2 = BASE.sig2
rng = random.Random(0)
sd = math.sqrt

print("== 1. Closed form vs Monte Carlo (60k runs), q=1e-6, twin gain")
ch = BASE.replace(q=1e-6)
g = gain_twin(ch, ST2)
for k in (10, 20, 30, 40):
    print("k=%2d  exact real var %.4e  mc %.4e | twin claims %.4e" % (k, real_var(ch, g, k), simulate(ch, g, k, 60000, rng), claimed_var(ch, ST2, k)))

print("\n== 2. A constant shared drift is absorbed (n=40, twin gain): worst-pose sd, drift sd beta")
for beta in (0.0, 0.002, 0.004, 0.02):
    c = BASE.replace(q=0.0)
    # constant drift b ~ N(0, beta^2): S_k = k b + noise, so v_k += k^2 beta^2, a_k += k n beta^2; evaluate the same formula directly
    n = c.n
    W = n * c.sig2 + n * n * beta ** 2 + c.sc2
    gt = gain_twin(c, ST2)
    w = max(k * c.sig2 + k * k * beta ** 2 - 2 * gt * k * (k * c.sig2 + k * n * beta ** 2) + (gt * k) ** 2 * W for k in range(1, n + 1))
    print("beta=%.3f  real worst sd %.5f (twin claims %.5f)" % (beta, sd(w), sd(worst_claimed(c, ST2))))

print("\n== 3. Drifting bias (random walk, per-step variance q): twin's claim vs reality, worst pose")
print("%-8s %-11s %-10s %-10s %-10s %-11s %-11s" % ("q", "claimed sd", "real sd", "end-gain", "per-pose", "real/claim", "gain g n: twin / end"))
for q in (1e-7, 1e-6, 4e-6, 1e-5):
    ch = BASE.replace(q=q)
    t = cov_terms(ch)
    gt, ge = gain_twin(ch, ST2), gain_end(ch)
    wr = max(real_var(ch, gt, k, t) for k in range(1, 41))
    we = max(real_var(ch, ge, k, t) for k in range(1, 41))
    wo = max(profile_opt(ch, k, t) for k in range(1, 41))
    wc = worst_claimed(ch, ST2)
    print("%-8.0e %-11.5f %-10.5f %-10.5f %-10.5f %-11.2f %.4f / %.4f" % (q, sd(wc), sd(wr), sd(we), sd(wo), sd(wr) / sd(wc), gt * 40, ge * 40))

print("\n== 4. Certified chain length: largest n with worst-pose sd <= 4 cm (tau2 = 1.6e-3)")
tau2 = 1.6e-3
print("%-8s %-15s %-17s %-19s %-22s" % ("q", "twin certifies", "real sd there", "true max n (twin g)", "true max n (end gain)"))
for q in (1e-7, 1e-6, 4e-6):
    base = BASE.replace(q=q)
    nt = max_length_claimed(base, ST2, tau2)
    c = base.replace(n=nt)
    print("%-8.0e %-15d %-17.5f %-19d %-22d" % (q, nt, sd(worst(c, gain_twin(c, ST2))), max_length_real(base, tau2, lambda x: gain_twin(x, ST2)), max_length_real(base, tau2, gain_end)))

print("\n== 5. Auditing the claim: one-sided test on the mean of m squared errors at pose k=20 over the twin's claim (5% level, 20000 draws)")
print("%-8s %-8s | power at m = 1, 3, 10, 30, 100" % ("q", "ratio"))
for q in (1e-7, 1e-6, 4e-6):
    ch = BASE.replace(q=q)
    ratio = nees_ratio(ch, ST2, 20)
    pw = [nees_power(ratio, m, rng)[0] for m in (1, 3, 10, 30, 100)]
    print("%-8.0e %-8.2f | %s" % (q, ratio, "  ".join("%.3f" % x for x in pw)))
print("null false-alarm check (ratio 1): m=10 -> %.3f, m=100 -> %.3f" % (nees_power(1.0, 10, rng)[0], nees_power(1.0, 100, rng)[0]))
