"""Reproduces every number in paper/whitepaper.md. Run: PYTHONPATH=src python3 experiments/run.py > experiments/results.txt"""
import math
from radar_detection_twin import *

N = 16
KS = (8, 12, 14)  # OS ranks: N/2, 3N/4, 7N/8
grids = {}
G = lambda nu: grids.setdefault(nu, TextureGrid(nu))
db = lambda x: 10 * math.log10(x)
print("N=%d reference cells, independent gamma texture per cell (shape nu), twin = Gaussian clutter, OS ranks k=%s" % (N, KS))


def dets(nu):
    """(name, exceedance fn) for CA and each OS rank; nu=None is the Gaussian twin."""
    g = None if nu is None else G(nu)
    out = [("CA", pd_fn("ca", N, grid=g))]
    out += [("OS k=%d" % k, pd_fn("os", N, k, g)) for k in KS]
    return out


print("\n== 1. Real Pfa when the threshold is set in the Gaussian twin ==")
print("design Pfa  nu    " + "  ".join("%-16s" % n for n, _ in dets(None)))
for pf in (1e-2, 1e-4, 1e-6):
    tw = dets(None)
    al = [alpha_for_pfa(pf, f) for _, f in tw]
    for nu in (2, 5, 20):
        row = ["%.2e (%.1fx)" % (f(a, 0), f(a, 0) / pf) for a, (_, f) in zip(al, dets(nu))]
        print("%-10g  %-4g  %s" % (pf, nu, "  ".join("%-16s" % r for r in row)))

print("\n== 2. Quadrature laws vs direct Monte Carlo (design Pfa 1e-2, 400k trials) ==")
for nu in (2, 5):
    for name, kind, k in (("CA", "ca", None), ("OS k=12", "os", 12)):
        f = pd_fn(kind, N, k, None)
        a = alpha_for_pfa(1e-2, f)
        ex = pd_fn(kind, N, k, G(nu))
        print("nu=%d %-8s MC Pfa %.4f quadrature %.4f | shared texture MC %.4f (twin design 0.0100)" % (
            nu, name, simulate(a, N, nu, 400000, 5 + nu, kind, k), ex(a, 0), simulate(a, N, nu, 400000, 50 + nu, kind, k, shared=True)))
    s = 8.0
    for name, kind, k in (("CA", "ca", None), ("OS k=12", "os", 12)):
        a = alpha_for_pfa(1e-2, pd_fn(kind, N, k, None))
        print("nu=%d %-8s target SNR %.0f (%.1f dB): MC Pd %.4f quadrature %.4f" % (
            nu, name, s, db(s), simulate(a, N, nu, 400000, 70 + nu, kind, k, snr=s), pd_fn(kind, N, k, G(nu))(a, s)))

print("\n== 3. Threshold multiplier restoring design Pfa in real clutter (vs the twin's), design 1e-4 ==")
print("nu   " + "  ".join("%-20s" % n for n, _ in dets(None)))
for nu in (2, 5, 20):
    row = []
    for (_, ft), (_, fr) in zip(dets(None), dets(nu)):
        at, ar = alpha_for_pfa(1e-4, ft), alpha_for_pfa(1e-4, fr)
        row.append("%.2fx (%.2f dB)" % (ar / at, db(ar / at)))
    print("%-4g %s" % (nu, "  ".join("%-20s" % r for r in row)))

print("\n== 4. SNR needed for Pd=0.9 at Pfa 1e-4 (dB, relative to local clutter mean) ==")
print("twin promise = threshold and Pd both computed in the Gaussian twin; real = repaired threshold (real Pfa 1e-4) and real Pd")
print("detector    twin promise   " + "  ".join("real nu=%-6g" % nu for nu in (2, 5, 20)) + "   shortfall (real - promise) dB")
tw = dets(None)
for i, (name, ft) in enumerate(tw):
    prom = snr_for_pd(ft, alpha_for_pfa(1e-4, ft), 0.9)
    reals = []
    for nu in (2, 5, 20):
        fr = dets(nu)[i][1]
        reals.append(snr_for_pd(fr, alpha_for_pfa(1e-4, fr), 0.9))
    print("%-10s  %-13.2f  %s   %s" % (name, db(prom), "  ".join("%-13.2f" % db(r) for r in reals),
                                       "  ".join("%.2f" % (db(r) - db(prom)) for r in reals)))

print("\n== 5. Detector ranking: best detector by SNR needed for Pd=0.9 at Pfa 1e-4 (dB relative to CA in the same world) ==")
print("world       " + "  ".join("%-9s" % n for n, _ in dets(None)) + "  best")
for label, nu in (("twin", None), ("nu=20", 20), ("nu=5", 5), ("nu=2", 2), ("nu=1.5", 1.5)):
    d = dets(nu)
    need = [snr_for_pd(f, alpha_for_pfa(1e-4, f), 0.9) for _, f in d]
    print("%-10s  %s  %s" % (label, "  ".join("%-9.2f" % (db(x) - db(need[0])) for x in need), d[need.index(min(need))][0]))

print("\n== 6. What the uncalibrated twin threshold does to Pd (Pd 0.9 target SNR from the twin promise, design Pfa 1e-4) ==")
print("detector   nu   real Pfa      real Pd at promised SNR")
for i, (name, ft) in enumerate(tw):
    at = alpha_for_pfa(1e-4, ft)
    s = snr_for_pd(ft, at, 0.9)
    for nu in (2, 5):
        fr = dets(nu)[i][1]
        print("%-9s  %-3g  %-12.2e  %.3f" % (name, nu, fr(at, 0), fr(at, s)))

print("\n== 7. Numerical accuracy of the quadrature (it is a grid quadrature, not a closed form) ==")
# (a) Degenerate texture (tau = 1): the same OS order-statistic integral and CA table must reproduce the closed-form twin laws.
g1 = TextureGrid(2.0)
g1.tau, g1.w = [1.0], [1.0]
g1.g = [1 / (1 + math.exp(g1.slo + j * g1.hs)) for j in range(len(g1.g))]
g1.S = [math.exp(-x) for x in g1.z]
g1.logS = [math.log(s) if s > 1e-300 else -690.0 for s in g1.S]
errs = []
for pf in (1e-2, 1e-4, 1e-6):
    a = alpha_ca_twin(pf, N)
    errs.append(abs(pfa_ca_real(a, N, g1) / pf - 1))
    for k in KS:
        a = alpha_os_twin(pf, N, k)
        errs.append(abs(pfa_os_real(a, N, k, g1) / pf - 1))
print("texture fixed at 1, quadrature vs closed-form twin Pfa (CA, OS k=8/12/14; design 1e-2/1e-4/1e-6): max relative error %.1e" % max(errs))
# (b) Grid refinement in textured clutter: double every grid resolution and compare.
g2 = TextureGrid(2.0, n=1000, ns=960, nz=6000)
errs = []
for pf in (1e-2, 1e-4, 1e-6):
    for kind, k in (("ca", None),) + tuple(("os", k) for k in KS):
        a = alpha_for_pfa(pf, pd_fn(kind, N, k, None))
        for s in (0.0, 8.0):
            errs.append(abs(pd_fn(kind, N, k, G(2))(a, s) / pd_fn(kind, N, k, g2)(a, s) - 1))
print("nu=2, all grids doubled: max relative change in Pfa and Pd (SNR 8) over CA, OS k=8/12/14 at twin thresholds for design 1e-2/1e-4/1e-6: %.1e" % max(errs))
rse = lambda q: math.sqrt((1 - q) / (400000 * q))
pf2 = [pd_fn(kind, N, k, G(nu))(alpha_for_pfa(1e-2, pd_fn(kind, N, k, None)), s) for nu in (2, 5) for kind, k in (("ca", None), ("os", 12)) for s in (0.0,)]
pd2 = [pd_fn(kind, N, k, G(nu))(alpha_for_pfa(1e-2, pd_fn(kind, N, k, None)), 8.0) for nu in (2, 5) for kind, k in (("ca", None), ("os", 12))]
print("Monte Carlo relative standard error in section 2 (400k trials): Pfa %.1f-%.1f%%, Pd %.2f-%.2f%%, so those checks cannot resolve quadrature errors this small" % (
    100 * min(map(rse, pf2)), 100 * max(map(rse, pf2)), 100 * min(map(rse, pd2)), 100 * max(map(rse, pd2))))
