"""Reproduces every number in paper/whitepaper.md. Run: PYTHONPATH=src python3 experiments/run.py > experiments/results.txt"""
import math
import random
from sag_twin.model import (v_end, runtime_real, runtime_twin, runtime_numeric, efficiency, p_start, hover_power, max_payload)

V0, M, C, VC = 25.2, 1.44, 5.0, 19.8
P0, M0, TAU = 150.0, 1.0, 20 / 60  # hover power at the 1 kg airframe, airframe mass, required hover time (h)
RS = (0.03, 0.06, 0.12, 0.24)

print("Sag twin: 6S pack, OCV 25.2 -> 18.0 V linear over C = %.0f Ah, cutoff %.1f V under load; real = series resistance R, twin = R = 0 (energy bucket)" % (C, VC))
print("twin energy claim = %.1f Wh" % ((V0 ** 2 - (V0 - M * C) ** 2) / (2 * M)))

print("\n== 1. Closed form vs numerical integration of dt = dx/I (minutes) ==")
print("  R (ohm)  P (W)   closed form    numeric     twin")
for R in (0.06, 0.24):
    for P in (150, 300, 450):
        print("  %-6g   %4d    %9.4f    %9.4f   %9.4f" % (R, P, 60 * runtime_real(P, R, V0, M, C, VC), 60 * runtime_numeric(P, R, V0, M, C, VC, 200000), 60 * runtime_twin(P, V0, M, C, VC)))

print("\n== 2. Delivered fraction of the twin's energy claim, eta = real / twin runtime ==")
print("  P (W)   " + "   ".join("R=%.2f" % R for R in RS))
for P in (50, 100, 150, 250, 350, 450, 550):
    print("  %4d    " % P + "   ".join("%6.3f" % efficiency(P, R, V0, M, C, VC) for R in RS))

print("\n== 3. A twin with one calibrated constant efficiency (fitted at P = 150 W, R = 0.12) vs the real runtime ==")
eta0 = efficiency(150, 0.12, V0, M, C, VC)
print("  calibrated eta = %.4f" % eta0)
print("  P (W)   real (min)   twin (min)   calibrated twin (min)   calibrated error")
for P in (50, 100, 150, 250, 350, 450):
    r = runtime_real(P, 0.12, V0, M, C, VC)
    c = eta0 * runtime_twin(P, V0, M, C, VC)
    print("  %4d    %7.2f      %7.2f       %7.2f              %+6.1f%%" % (P, 60 * r, 60 * runtime_twin(P, V0, M, C, VC), 60 * c, 100 * (c / r - 1)))
print("  the ideal twin overstates real runtime by 1/eta - 1; at R = 0.12:")
for P in (150, 350, 450):
    print("    P = %d W: %+.1f%%" % (P, 100 * (1 / efficiency(P, 0.12, V0, M, C, VC) - 1)))

print("\n== 4. Largest power with a non-empty flight, P_start = Vc (V0 - Vc) / R; the energy twin has no such limit ==")
for R in RS:
    print("  R = %.2f   P_start = %7.1f W   (%.2f x the 150 W hover power)" % (R, p_start(R, V0, VC), p_start(R, V0, VC) / P0))

print("\n== 5. Max payload for a %.0f-minute hover (%.0f W at %.0f kg, power ~ mass^1.5): twin vs real ==" % (TAU * 60, P0, M0))
tw = lambda P: runtime_twin(P, V0, M, C, VC)
pt = max_payload(TAU, P0, M0, tw)
print("  twin payload = %.3f kg (hover power %.0f W)" % (pt, hover_power(M0 + pt, P0, M0)))
print("  R (ohm)   real payload (kg)   twin overstates payload by   real hover power at twin payload   real runtime there (min)")
for R in RS:
    re = lambda P, R=R: runtime_real(P, R, V0, M, C, VC)
    pr = max_payload(TAU, P0, M0, re)
    Ptw = hover_power(M0 + pt, P0, M0)
    print("  %.2f      %8.3f            %6.1f%%                       %7.1f                            %6.2f" % (R, pr, 100 * (pt / pr - 1), Ptw, 60 * re(Ptw)))

print("\n== 6. Fleet with lognormal resistance R = 0.12 exp(0.35 z) (cold, aged and cheap packs): shortfall at the twin's payload ==")
R0, SIG = 0.12, 0.35
Ptw = hover_power(M0 + pt, P0, M0)
print("  the twin's payload sits on its own boundary (runtime exactly %.0f min at R = 0), so every pack with R > 0 falls short: failure probability 1 by construction" % (TAU * 60))
print("  the informative quantity is the shortfall; real runtime at the twin's payload (%.0f W), exact quantiles of the R distribution (runtime falls in R):" % Ptw)
for q, z in ((0.5, 0.0), (0.9, 1.2816), (0.95, 1.6449), (0.99, 2.3263)):
    t = 60 * runtime_real(Ptw, R0 * math.exp(SIG * z), V0, M, C, VC)
    print("    %.0f%% of packs run no longer than %5.2f min (%.0f%% short)" % (100 * (1 - q), t, 100 * (1 - t / (TAU * 60))))
rng = random.Random(3)
n = 200000
ts = sorted(60 * runtime_real(Ptw, R0 * math.exp(SIG * rng.gauss(0, 1)), V0, M, C, VC) for _ in range(n))
print("  Monte Carlo (%d packs): median %.2f min, 5th percentile %.2f min, 1st percentile %.2f min" % (n, ts[n // 2], ts[n // 20], ts[n // 100]))
print("  payload so that a fraction eps of packs fall short (sized at the (1-eps) quantile of R) and its cost vs the twin payload:")
print("  eps      z       R_q (ohm)   payload (kg)   cut vs twin")
for eps, z in ((0.5, 0.0), (0.1, 1.2816), (0.05, 1.6449), (0.01, 2.3263)):
    Rq = R0 * math.exp(SIG * z)
    pq = max_payload(TAU, P0, M0, lambda P: runtime_real(P, Rq, V0, M, C, VC))
    print("  %.2f    %.3f    %.4f      %.3f          %5.1f%%" % (eps, z, Rq, pq, 100 * (pq / pt - 1)))
