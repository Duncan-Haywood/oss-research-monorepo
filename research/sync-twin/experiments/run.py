"""Reproduces every number in paper/whitepaper.md. Run: PYTHONPATH=src python3 experiments/run.py > experiments/results.txt"""
import math, random
from sync_twin import *

SIG, R = 0.2, 0.99
G = design_gate(SIG, R)
print("Two sensors report a target's position with independent N(0, 0.2^2) m noise; B's timestamp is off by delta (twin: 0).")
print("The twin picks the association gate for %.0f%% recall of true pairs with delta=0: g = %.4f m = 2.576*sqrt(2)*sigma." % (100 * R, G))
print("v = target speed (m/s), s = timestamp jitter sd (ms), kappa = 1 + v^2 s^2/(2 sigma^2).")

print("\n== 0. Recall of the twin's gate: exact formula vs simulation (200000 pairs per row) ==")
print("v     s(ms)  v*s(m)  kappa   recall formula  simulated")
rng = random.Random(1)
for v, s in ((5, 0.010), (10, 0.010), (10, 0.020), (20, 0.020), (20, 0.050)):
    n = 200000
    hit = sum(abs(b - a) < G for a, b in sim_diffs(rng, SIG, v, s, n)) / n
    print("%-5g %-6g %-7.3f %-7.3f %-15.4f %.4f" % (v, 1000 * s, v * s, kappa(SIG, v, s), recall_jitter(G, SIG, v, s), hit))

print("\n== 1. Recall of the twin's 99% gate by speed and jitter (exact) ==")
print("Twin's own recall is 0.990 at every speed and jitter.")
print("s(ms)  " + "  ".join("v=%-4g" % v for v in (2, 5, 10, 20, 30)) + "   speed at which recall falls to 0.95 / 0.90 (m/s)")
for s in (0.005, 0.010, 0.020, 0.050):
    print("%-6g " % (1000 * s) + "  ".join("%.3f " % recall_jitter(G, SIG, v, s) for v in (2, 5, 10, 20, 30)) +
          "   %.1f / %.1f" % (speed_at_recall(G, SIG, s, 0.95), speed_at_recall(G, SIG, s, 0.90)))

print("\n== 2. Constant offset vs jitter of the same rms shift v*s (recall of the twin's gate, exact) ==")
print("v     shift(m)  jitter recall  constant-offset recall")
for v, s in ((10, 0.010), (10, 0.020), (20, 0.020), (20, 0.030)):
    print("%-5g %-9.3f %-14.4f %.4f" % (v, v * s, recall_jitter(G, SIG, v, s), recall_bias(G, SIG, v, s)))

print("\n== 3. Fusion: equal weights (the twin's choice) vs the optimal weight, MSE in units of sigma^2 (400000 draws per cell) ==")
print("The twin says equal-weight fusion has MSE 0.5 sigma^2 at every speed; a single sensor A has MSE 1.")
print("v     s(ms)  kappa   equal-w formula  equal-w simulated  w_opt   opt formula  opt simulated")
rng = random.Random(2)
for v, s in ((5, 0.010), (10, 0.020), (20, 0.020), (20, 0.050)):
    e = fused_mse(SIG, v, s, 0.5) / SIG ** 2
    es = sim_fused_mse(rng, SIG, v, s, 0.5, 400000) / SIG ** 2
    w = w_opt(SIG, v, s)
    o = mse_opt(SIG, v, s) / SIG ** 2
    os_ = sim_fused_mse(rng, SIG, v, s, w, 400000) / SIG ** 2
    print("%-5g %-6g %-7.3f %-16.4f %-18.4f %-7.4f %-12.4f %.4f" % (v, 1000 * s, kappa(SIG, v, s), e, es, w, o, os_))
print("Equal-weight fusion is worse than sensor A alone once kappa > 2, i.e. v*s > sqrt(2)*sigma = %.3f m." % (math.sqrt(2) * SIG))

print("\n== 4. Repairing the gate: inflate by sqrt(kappa) to restore 99% recall, and what it costs in neighbour confusion ==")
print("A second target moving alike lies D metres away; confusion = P(its detection falls inside the gate) (exact).")
print("v     s(ms)  kappa   gate twin  gate repaired  D(m)   confusion twin gate  confusion repaired gate  confusion with delta=0 twin")
for v, s in ((10, 0.020), (20, 0.020), (20, 0.050)):
    g2 = gate_repair(SIG, v, s, R)
    for D in (1.0, 0.7):
        print("%-5g %-6g %-7.3f %-10.4f %-14.4f %-6g %-20.4f %-24.4f %.4f" % (
            v, 1000 * s, kappa(SIG, v, s), G, g2, D, neighbour_assoc(G, D, SIG, v, s), neighbour_assoc(g2, D, SIG, v, s),
            neighbour_assoc(G, D, SIG, v, 0.0)))
