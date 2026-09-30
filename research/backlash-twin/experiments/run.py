"""Reproduces every number in paper/whitepaper.md. Run: PYTHONPATH=src python3 experiments/run.py > experiments/results.txt"""
from backlash_twin.model import *

K, D, P = 0.5, 0.1, 10
print("Backlash twin: motor integrates the error, load coupled through play half-width d=%g; K=%g, half-period P=%d steps." % (D, K, P))
print("Reference: square wave +-A/2. Twin has no play. 'swing' = load half peak-to-peak, 'err' = stationary rms tracking error.")

print("\n== 1. Exact twin vs simulation (linear twin, no play) ==")
print("A      twin swing (exact)  simulated   twin err (exact)  simulated")
for A in (0.05, 0.2, 1.0):
    sw, er = measure(simulate_twin(K, P, A), P)
    print("%-6g %-19.6f %-11.6f %-17.6f %.6f" % (A, twin_amplitude(K, P, A), sw, twin_rms_error(K, P, A), er))

print("\n== 2. Real loop: coexisting outcomes by initial gap g0 in {-d,-d/2,0,d/2,d} (x0=0, 200 periods) ==")
print("stuck-at-0 consistent iff K*P*A/2 <= 2d, i.e. A <= %.4f" % (4 * D / (K * P)))
print("A       twin swing/err       exact moving cycles (n, swing)      swing/err per g0")
for A in (0.03, 0.05, 0.06, 0.065, 0.07, 0.075, 0.08, 0.085, 0.1, 0.2, 0.5, 1.0):
    cyc = cycle_candidates(K, D, P, A)
    res = []
    for g0 in (-D, -D / 2, 0.0, D / 2, D):
        sw, er = measure(simulate(K, D, P, A, g0=g0), P)
        res.append("%.4f/%.4f" % (sw, er))
    print("%-7g %.4f/%.4f    %-34s %s" % (A, twin_amplitude(K, P, A), twin_rms_error(K, P, A),
                                        ",".join("(%d, %.4f)" % c for c in cyc) or "none", " ".join(res)))

print("\n== 3. Exact cycle rms error vs simulation (unique-cycle regime) ==")
print("A      n   exact err  simulated err   twin err   real/twin")
for A in (0.1, 0.2, 0.5, 1.0):
    (n, a), = cycle_candidates(K, D, P, A)
    er_sim = measure(simulate(K, D, P, A), P)[1]
    print("%-6g %-3d %-10.6f %-15.6f %-10.6f %.3f" % (A, n, cycle_error_rms(K, D, P, A, n, a), er_sim,
                                                      twin_rms_error(K, P, A), er_sim / twin_rms_error(K, P, A)))

print("\n== 4. Stuck-at-0 threshold A_s = 4d/(K P) shrinks as 1/P while the real/twin error ratio at A just below A_s grows (g0=-d, stuck) ==")
print("P      A_s      stuck err (=A_s/2)   twin err   ratio")
for p in (5, 10, 20, 40):
    A = 4 * D / (K * p)
    er = measure(simulate(K, D, p, A * 0.999, g0=-D), p)[1]
    tw = twin_rms_error(K, p, A * 0.999)
    print("%-6d %-8.4f %-20.4f %-10.4f %.1f" % (p, A, er, tw, er / tw))
