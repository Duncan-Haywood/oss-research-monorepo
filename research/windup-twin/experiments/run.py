"""Reproduces every number in paper/whitepaper.md. Run: PYTHONPATH=src python3 experiments/run.py > experiments/results.txt"""
import math
from windup_twin.model import (gains, twin_overshoot, exit_time, real_overshoot, clamped_overshoot, simulate,
                               overshoot_of)

U = 1.0
print("Windup twin: integrator plant x' = -sat_U(kp x + ki z), z' = x, x(0) = x0, z(0) = 0; kp = 2 zeta wn, ki = wn^2.")
print("a = kp x0 / U is the saturation depth of the first command; the twin has no saturation. Undershoot = -min x / x0.")


def sim(x0, wn, zeta, mode):
    return overshoot_of(simulate(x0, U, wn, zeta, 60.0 / wn + 4 * x0 / U, 1e-3 / wn, mode), x0)


print("\n== 1. Exact real undershoot vs RK4 simulation, wn = 1 ==")
print("zeta  a     twin(formula) twin(sim)  real(formula) real(sim)   real/twin   exit time t1")
for zeta in (0.7, 1.0, 2.0):
    kp, ki = gains(1.0, zeta)
    for a in (0.5, 1, 2, 5, 20, 100):
        x0 = a * U / kp
        t1 = exit_time(x0, U, kp, ki)
        r, tw = real_overshoot(x0, U, 1.0, zeta), twin_overshoot(1.0, zeta)
        print("%-5g %-5g %-13.5f %-10.5f %-13.5f %-11.5f %-11.3f %s" % (
            zeta, a, tw, sim(x0, 1.0, zeta, "twin"), r, sim(x0, 1.0, zeta, "none"), r / tw,
            "-" if t1 is None else "%.4f" % t1))

print("\n== 2. Deep-saturation limit: 1 - real undershoot -> kp U/(ki x0) = 4 zeta^2 / a, so the undershoot -> 100% ==")
print("zeta  (1-os)*a/(4 zeta^2) at a = 10, 100, 1e3, 1e4, 1e5      limit ratio real/twin = 1/twin")
for zeta in (0.3, 0.7, 1.0, 2.0):
    kp, ki = gains(1.0, zeta)
    row = ["%.4f" % ((1 - real_overshoot(a * U / kp, U, 1.0, zeta)) * a / (4 * zeta ** 2)) for a in (10, 100, 1e3, 1e4, 1e5)]
    print("%-5g %-52s %.3f" % (zeta, "  ".join(row), 1 / twin_overshoot(1.0, zeta)))

print("\n== 3. Conditional integration (freeze z while saturated and v pushes deeper): absolute undershoot = twin(x0 = U/kp) ==")
print("zeta  a     clamp(formula) clamp(sim)   windup(sim)   twin(sim)")
for zeta in (0.3, 0.7, 1.0, 2.0):
    kp, ki = gains(1.0, zeta)
    for a in (2, 20, 100):
        x0 = a * U / kp
        print("%-5g %-5g %-14.5f %-12.5f %-13.5f %-10.5f" % (zeta, a, clamped_overshoot(x0, U, 1.0, zeta), sim(x0, 1.0, zeta, "clamp"),
                                                            sim(x0, 1.0, zeta, "none"), sim(x0, 1.0, zeta, "twin")))
print("(zeta = 0.3: the replayed trajectory itself saturates on the far side, so the formula is an upper bound there.)")

print("\n== 4. Design: largest saturation depth a* (real undershoot <= target); twin certifies any bandwidth ==")
print("zeta  twin undershoot   a* for target 0.25, 0.30, 0.40, 0.50")


def astar(zeta, target):
    lo, hi = 1.0, 1e6
    kp, ki = gains(1.0, zeta)
    for _ in range(200):
        m = math.sqrt(lo * hi)
        if real_overshoot(m * U / kp, U, 1.0, zeta) <= target:
            lo = m
        else:
            hi = m
    return lo


for zeta in (0.7, 1.0, 2.0):
    print("%-5g %-16.5f %s" % (zeta, twin_overshoot(1.0, zeta), "  ".join("%.3f" % astar(zeta, t) for t in (0.25, 0.3, 0.4, 0.5))))

print("\n== 5. Same loop, fixed command size: bandwidth wn vs undershoot (zeta = 1, x0 = 1, U = 1 so a = 2 wn) ==")
print("wn     a      twin     real(formula)  real(sim)  clamp(sim)")
for wn in (0.25, 0.5, 1, 2, 5, 10, 50):
    a = 2 * wn
    print("%-6g %-6g %-8.4f %-14.4f %-10.4f %.4f" % (wn, a, twin_overshoot(wn, 1.0), real_overshoot(1.0, U, wn, 1.0),
                                                     sim(1.0, wn, 1.0, "none"), sim(1.0, wn, 1.0, "clamp")))
