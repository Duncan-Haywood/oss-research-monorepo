"""Reproduces every number in paper/whitepaper.md. Run: PYTHONPATH=src python3 experiments/run.py > experiments/results.txt"""
import math
from sweep_twin.model import (walls_rectangle, scan, sector, fit_line, wall_yaw, skew_formula, speed_limit, deskew, deskew_residual,
                              deskew_tolerance, room_heading, wrap)

T, HW = 0.1, math.radians(30)
ROOM = walls_rectangle(-5, 5, -5, 5)
deg = math.degrees
print("Sweep twin: real = spinning 2-D lidar, scan period T=%g s (10 Hz), 1800 beams, moving robot; twin = whole scan at one instant." % T)
print("Wall fitted by total least squares over +-30 deg of azimuth; skew = error of the fitted wall normal angle.\n")

print("== 1. Wall 5 m ahead, robot driving at it: apparent rotation of the wall (twin: 0) ==")
print("v (m/s)   fitted skew (deg)   fitted distance (m)   formula vn T/(2 pi d0) (deg)   formula with d at hit (deg)")
for v in (1, 2, 5, 10, 20):
    psi, d = wall_yaw(scan(ROOM, v=(v, 0), T=T), 0.0, HW)
    print("%6.1f   %17.3f   %19.3f   %28.3f   %27.3f" % (v, deg(psi), d, deg(skew_formula(v, T, 5.0)), deg(skew_formula(v, T, d))))

print("\n== 2. Only the normal velocity component skews a wall (v = 10 m/s, wall 5 m ahead) ==")
for name, v in (("normal   (10, 0)", (10, 0)), ("tangent  (0, 10)", (0, 10)), ("oblique (7.07, 7.07)", (7.07, 7.07))):
    psi, d = wall_yaw(scan(ROOM, v=v, T=T), 0.0, HW)
    print("%-22s skew %.3f deg, fitted distance %.3f m" % (name, deg(psi), d))

print("\n== 3. Scan period and range: skew at v = 10 m/s ==")
print("T (s)    d=2 m    d=5 m    d=10 m   (deg, fitted; wall ahead)")
for Tp in (0.05, 0.1, 0.2):
    row = []
    for d in (2.0, 5.0, 10.0):
        room = walls_rectangle(-20, d, -20, 20)
        row.append(deg(wall_yaw(scan(room, v=(10, 0), T=Tp), 0.0, HW)[0]))
    print("%5.2f  %7.3f  %7.3f  %8.3f" % (Tp, *row))

print("\n== 4. Room heading estimate from all four walls (walls weighted by point count, +-5 deg sectors), robot at origin, v = (5, 0) m/s ==")
cs = [0.0, math.pi / 2, math.pi, -math.pi / 2]
HW4 = math.radians(5)        # narrow sector so that no sector reaches a corner in any of these rooms
for name, room in (("centred  x in [-5, 5]", walls_rectangle(-5, 5, -5, 5)), ("off-centre x in [-2, 18]", walls_rectangle(-2, 18, -5, 5)),
                   ("long hall x in [-2, 40]", walls_rectangle(-2, 40, -5, 5))):
    e, errs = room_heading(scan(room, v=(5, 0), T=T), cs, HW4)
    twin, _ = room_heading(scan(room, T=T), cs, HW4)
    print("%-26s mean heading error %.3f deg (twin %.1e); per wall (front, left, back, right) = %s deg" % (name, deg(e), twin, [round(deg(x), 3) for x in errs]))

print("\n== 5. Speed limit for a skew tolerance: v* = 2 pi d psi_tol / T (m/s) ==")
print("tolerance   T (s)   d=2 m   d=5 m   d=10 m")
for tol in (0.5, 1.0, 2.0):
    for Tp in (0.05, 0.1):
        print("%6.1f deg  %5.2f  %6.2f  %6.2f  %7.2f" % (tol, Tp, *[speed_limit(math.radians(tol), Tp, d) for d in (2.0, 5.0, 10.0)]))
psi_chk, d_chk = wall_yaw(scan(walls_rectangle(-5, 5, -5, 5), v=(speed_limit(math.radians(1.0), T, 5.0), 0), T=T), 0.0, HW)
print("check: at v*(1 deg, T=0.1, d=5) = %.2f m/s the fitted skew is %.3f deg (fitted distance %.3f m)" % (speed_limit(math.radians(1.0), T, 5.0), deg(psi_chk), d_chk))

print("\n== 6. Deskewing with a wrong velocity (true v = 10 m/s, wall 5 m ahead, T = 0.1 s) ==")
print("velocity error   residual skew (deg)   formula (vn - v_est) T/(2 pi d_hit) (deg)")
v = 10.0
d_hit = wall_yaw(scan(ROOM, v=(v, 0), T=T), 0.0, HW)[1]
for eps in (0.0, 0.05, 0.1, 0.2, 0.5):
    pts = deskew(scan(ROOM, v=(v, 0), T=T), ((1 - eps) * v, 0))
    r = wrap(fit_line(sector(pts, 0.0, HW))[0])
    print("%12.0f%%   %18.3f   %38.3f" % (100 * eps, deg(r), deg(deskew_residual(v, (1 - eps) * v, T, d_hit + 0 * eps))))
for tol in (0.5, 1.0):
    print("velocity accuracy needed for residual <= %.1f deg at v=10, d=5, T=0.1: eps <= %.1f%%" % (tol, 100 * deskew_tolerance(math.radians(tol), v, T, 5.0)))

print("\n== 7. Yaw rate bends the wall instead of rotating it (wall 5 m ahead, +-20 deg sector, no translation) ==")
print("yaw rate (rad/s)   max departure from best line (mm)   fitted tilt (deg)   heading at hit Om*t_hit (deg)   tilt minus heading (deg)")
for om in (0.5, 1.0, 2.0, 4.0):
    pts = sector(scan(ROOM, yaw_rate=om, T=T), 0.0, math.radians(20))
    a, d = fit_line(pts)
    dev = max(abs(x * math.cos(a) + y * math.sin(a) - d) for x, y, _ in pts)
    hh = deg(om * 0.375 * T)
    print("%15.1f   %33.3f   %17.3f   %29.3f   %24.3f" % (om, 1000 * dev, deg(wrap(a)), -hh, deg(wrap(a)) + hh))
