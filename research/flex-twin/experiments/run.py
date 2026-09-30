"""Reproduces every number in paper/whitepaper.md. Run: PYTHONPATH=src python3 experiments/run.py > experiments/results.txt"""
import math
from flex_twin.model import *

print("Flex twin: real plant = motor + spring/damper + load, twin = rigid body J=1.  PD on the load (non-collocated) or motor (collocated).")
print("Units: resonance wr = 1; design kp = wn^2, kd = 2*zeta*wn; zs = structural damping ratio; r = Jl/Jm.")

print("\n== 1. First-crossing bandwidth: closed form (cubic) vs roots of the characteristic polynomial (zeta=0.7) ==")
print("r      zs     wn* cubic    wn* roots    rel diff   wn*/zs")
worst = 0.0
for r in (0.25, 1, 4, 16):
    for zs in (0.01, 0.05, 0.2):
        a, b = wn_star(zs), max_stable_wn(r, zs)
        worst = max(worst, abs(a / b - 1))
        print("%-6g %-6g %-12.6f %-12.6f %-10.1e %.4f" % (r, zs, a, b, abs(a / b - 1), a / zs))
print("max relative difference = %.1e  (wn* is identical for all r: mu cancels)" % worst)

print("\n== 2. Does the twin's certificate hold?  Stable for ALL wn by construction.  Real abscissa max Re(pole), r=1, zs=0.05 ==")
print("wn/wn*    wn       real max Re(s)   twin max Re(s)   real growth/decay")
ws = wn_star(0.05)
for f in (0.25, 0.9, 1.1, 2, 5, 20):
    wn = f * ws
    kp, kd = design(wn)
    a = abscissa(char_poly(1.0, 0.05, kp, kd))
    tw = max(z.real for z in roots([1.0, kd, kp]))
    print("%-9g %-8.4f %-16.5f %-16.5f %s" % (f, wn, a, tw, "decays" if a < 0 else "GROWS e-fold in %.1f time units" % (1 / a)))
print("wn* = %.5f (zs=0.05): bandwidth must stay below %.1f%% of the resonance" % (ws, 100 * ws))

print("\n== 3. Time-domain check (RK4, dt=0.005, T=2000): |load| envelope, r=1, zs=0.2 ==")
ws = wn_star(0.2)
print("wn/wn*   max|q| in t in [600,800]   max|q| in t in [1800,2000]")
for f in (0.8, 0.98, 1.02, 1.25):
    kp, kd = design(f * ws)
    y = simulate(1.0, 0.2, kp, kd, 2000, dt=0.005)
    n = len(y)
    print("%-8g %-26.3e %.3e" % (f, max(abs(v) for v in y[int(600 / 0.005):int(800 / 0.005)]), max(abs(v) for v in y[int(1800 / 0.005):])))

print("\n== 4. Validation horizon: max|real - twin| of the load step response (x0=1, r=1, zs=0.05, dt=0.01) ==")
print("wn/wn*   real max Re(s)   T=50        T=400       T=3000")
ws = wn_star(0.05)
for f in (0.5, 0.99, 1.1, 2):
    kp, kd = design(f * ws)
    real = simulate(1.0, 0.05, kp, kd, 3000, dt=0.01)
    twin = simulate(1.0, 0.05, kp, kd, 3000, dt=0.01, twin=True)
    err = lambda T: max(abs(a - b) for a, b in zip(real[:int(T / 0.01)], twin[:int(T / 0.01)]))
    print("%-8g %-16.5f %-11.3e %-11.3e %.3e" % (f, abscissa(char_poly(1.0, 0.05, kp, kd)), err(50), err(400), err(3000)))

print("\n== 5. Structural damping needed for a target bandwidth (zeta=0.7) ==")
print("wn/wr   required zs   check: roots stable at 1.01*zs / unstable at 0.99*zs")
for wn in (0.05, 0.1, 0.2, 0.3, 0.5, 0.8):
    z = zs_required(wn)
    kp, kd = design(wn)
    print("%-7g %-13.5f %s / %s" % (wn, z, abscissa(char_poly(1.0, 1.01 * z, kp, kd)) < 0, abscissa(char_poly(1.0, 0.99 * z, kp, kd)) < 0))

print("\n== 6. Undamped joint (zs=0): max Re(pole) for the twin-certified design (r=1) ==")
for wn in (0.001, 0.01, 0.1, 1.0):
    kp, kd = design(wn)
    print("wn=%-6g max Re(s) = %.3e" % (wn, abscissa(char_poly(1.0, 0.0, kp, kd))))

print("\n== 7. Collocated (motor-side) feedback: stable at every gain (r=1, zs=0.05, zeta=0.7) ==")
print("wn      max Re(s)     twin max Re(s)")
for wn in (0.1, 1, 10, 50):
    kp, kd = design(wn)
    print("%-7g %-13.4e %.4e" % (wn, abscissa(char_poly(1.0, 0.05, kp, kd, collocated=True)), max(z.real for z in roots([1.0, kd, kp]))))

print("\n== 8. wn* scales as zs/zeta: lower design damping ratio allows more bandwidth (zs=0.05) ==")
for zeta in (0.3, 0.5, 0.7, 1.0, 2.0):
    print("zeta=%-4g wn* = %.5f  (zs/zeta = %.5f)" % (zeta, wn_star(0.05, zeta), 0.05 / zeta))
