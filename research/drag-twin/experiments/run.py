"""Reproduces every number in paper/whitepaper.md. Run: PYTHONPATH=src python3 experiments/run.py > experiments/results.txt"""
import math
import random
from drag_twin.model import *

K, V0 = 0.5, 10.0     # real drag k (1/m, unit mass), initial / top speed
print("Drag twin: real v' = F - k v^2 (k = %.2f, unit mass), twin v' = F - c v.  Closed-form truth; twin c fitted from coast-down." % K)

print("\n== 1. Coast-down from v0 = %.0f, twin calibrated by the secant at v0 (c = k v0 = %.1f): time / distance to reach v_f ==" % (V0, secant_c(K, V0)))
c = secant_c(K, V0)
print("v_f/v0   real time  twin time   real dist  twin dist")
for f in (0.5, 0.2, 0.1, 0.05, 0.01):
    vf = f * V0
    print("%-7.2f  %8.3f  %9.3f  %9.3f  %9.3f" % (f, real_time_to(vf, V0, K), twin_time_to(vf, V0, c), real_dist_to(vf, V0, K), twin_dist_to(vf, V0, c)))
print("twin stopping distance (v_f -> 0): %.3f; real distance to fall to 1e-6 v0: %.1f (unbounded, ln)" % (V0 / c, real_dist_to(1e-6 * V0, V0, K)))

print("\n== 2. Steady states and mission energy: twin secant-calibrated at v_cal, real system at other speeds ==")
print("for the force F = k v^2 that holds speed v in reality: twin terminal speed / v, and twin energy per distance / real (= v_cal/v)")
for vc in (3.0, 6.0, 10.0):
    cc = secant_c(K, vc)
    row = []
    for v in (2.0, 5.0, 10.0, 15.0):
        F = K * v * v                         # force that holds speed v in reality
        row.append("v=%-4g term %.3f energy %.3f" % (v, terminal_twin(F, cc) / terminal_real(F, K), energy_per_dist_twin(v, cc) / energy_per_dist_real(v, K)))
    print("v_cal=%-4g " % vc + " | ".join(row))

print("\n== 3. Step response of speed to a force step about v* = 6: time to cover 63.2% of the step (real vs twin) ==")
vs = 6.0
F0 = K * vs * vs
print("calibration   c        small step (+0.1%): real tau  twin tau   ratio    | large step F x4: real  twin  ratio    final speed twin/real")
for name, cc in (("secant ", secant_c(K, vs)), ("tangent", tangent_c(K, vs))):
    out = []
    for mult in (1.001, 4.0):
        F1 = F0 * mult
        r = time_to_fraction(lambda t: real_step_speed(t, vs, F1, K), vs, terminal_real(F1, K))
        w = time_to_fraction(lambda t: twin_step_speed(t, vs, F1, cc), vs, terminal_twin(F1, cc))
        out.append((r, w))
    F1 = 4 * F0
    print("%-11s  %.2f   %14.4f  %9.4f  %6.3f    | %12.4f %7.4f %6.3f    %.3f" % (
        name, cc, out[0][0], out[0][1], out[0][1] / out[0][0], out[1][0], out[1][1], out[1][1] / out[1][0], terminal_twin(F1, cc) / terminal_real(F1, K)))
print("closed-loop speed hold with proportional gain Kp (u = F0 + Kp (vref - v)), 10% step in vref, time to 63.2%: twin vs real (secant twin at v*)")
for Kp in (0.5, 2.0, 10.0):
    cc = secant_c(K, vs)
    vref = vs * 1.001
    # real closed loop: v' = F0 + Kp(vref - v) - K v^2 ; twin: v' = F0 + Kp(vref - v) - cc v ; integrate with RK4
    def sim(fdrag, dt=1e-3):
        v, t = vs, 0.0
        # steady state after step is found by iteration at fine dt; time to 63.2% of the way to the final value
        f = lambda v: F0 + Kp * (vref - v) - fdrag(v)
        vf = vs
        for _ in range(200000):
            vf += 1e-2 * f(vf)
        target = vs + (1 - math.exp(-1)) * (vf - vs)
        while v < target and t < 100:
            a = f(v); b = f(v + dt * a / 2); c2 = f(v + dt * b / 2); d = f(v + dt * c2)
            v += dt * (a + 2 * b + 2 * c2 + d) / 6
            t += dt
        return t
    tr, tw = sim(lambda v: K * v * v), sim(lambda v: cc * v)
    print("Kp=%-5g real %.4f  twin %.4f  ratio %.3f  (pole: real %.2f, twin %.2f)" % (Kp, tr, tw, tw / tr, 2 * K * vs + Kp, cc + Kp))

print("\n== 4. What a fit to coast-down data returns (v0 = %.0f, dt = 0.02, noise sd 0.05, mean of 20 seeds) ==" % V0)
print("window T   speed at T   fit on ln v (time domain)   fit on decel vs v   secant c at v0  at mid speed  tangent at v0")
for T in (0.2, 0.5, 1.0, 3.0):
    cs, ca = [], []
    for seed in range(20):
        d = coast_data(V0, K, 0.02, T, 0.05, random.Random(seed))
        cs.append(fit_c_from_speed(d))
        ca.append(fit_c_from_accel(d, 0.02))
    vT = real_coast_speed(T, V0, K)
    print("%-9.1f  %10.3f   %12.3f (sd %.3f)       %9.3f (sd %.3f)   %8.2f  %8.2f  %8.2f" % (
        T, vT, sum(cs) / 20, (sum((x - sum(cs) / 20) ** 2 for x in cs) / 19) ** .5, sum(ca) / 20,
        (sum((x - sum(ca) / 20) ** 2 for x in ca) / 19) ** .5, secant_c(K, V0), secant_c(K, 0.5 * (V0 + vT)), tangent_c(K, V0)))
print("noise-free force regression on v uniform on [0, V]: c = 3kV/4 (V=10: %.3f)" % ls_force_fit_c(K, 10.0))

print("\n== 5. A twin calibrated on a coast-down window [%.0f, %.0f] (mean-square fit of k v^2 by c v) used over a mission speed band: error of steady-state energy per distance ==" % (5.0, 10.0))
cc = ls_force_fit_c(K, 10.0, 5.0)
print("fitted c = %.3f (secant at the window midpoint 7.5 would be %.3f)" % (cc, K * 7.5))
for v in (1.0, 2.5, 5.0, 7.5, 10.0, 15.0):
    print("mission speed %-5g twin/real energy %.3f" % (v, energy_per_dist_twin(v, cc) / energy_per_dist_real(v, K)))
print("the fit is unbiased in the energy only at v = c/k = %.3f, and the twin over-charges slower and under-charges faster missions by the ratio v_fit/v" % (cc / K))
