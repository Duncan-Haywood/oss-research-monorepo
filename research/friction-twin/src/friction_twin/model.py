"""Friction twin.  Massless load with viscous damping (unit gain) driven through dry friction:
  stuck:   moves only if |u| > fs (static / breakaway level), then slides in the sign s of u
  sliding: x+ = x + u - s*fc while s*u > fc (Coulomb level fc <= fs), otherwise sticks again.
Loop (discrete PI, position measured): z+ = z + x, u = -(kp*x + ki*z+).
The twin has no dry friction (fs = fc = 0): x+ = x + u, characteristic polynomial z^2 - (2-kp-ki) z + (1-kp), so it
says the loop converges.  With fs = fc the friction is a pure deadband of the control signal (no stiction drop).
The dynamics are piecewise linear and positively homogeneous of degree 1 in (x, z, fs, fc): scaling the friction
levels and the initial condition by lambda scales the whole trajectory by lambda.
"""
import math


def run_loop(kp, ki, fs, fc, x0, n, z0=0.0):
    """Returns (xs, slips) of length n; slips[t] is the sliding sign (0 = stuck) during step t."""
    x, z, s = x0, z0, 0
    xs, slips = [], []
    for _ in range(n):
        z += x
        u = -(kp * x + ki * z)
        if s == 0 and abs(u) > fs:
            s = 1 if u > 0 else -1
        if s != 0:
            if s * u > fc:
                x += u - s * fc
            else:
                s = 0
        xs.append(x)
        slips.append(s)
    return xs, slips


def twin_radius(kp, ki):
    """Spectral radius of the frictionless loop."""
    tr, det = 2 - kp - ki, 1 - kp
    disc = tr * tr - 4 * det
    if disc >= 0:
        s = math.sqrt(disc)
        return max(abs(tr + s), abs(tr - s)) / 2
    return math.sqrt(det)


def amplitude(xs, tail=3000):
    t = xs[-tail:]
    return (max(t) - min(t)) / 2


def stick_slip_stats(xs, slips, tail=20000):
    """Cycle statistics over the tail: half-cycles are maximal stuck intervals; returns (number of stuck intervals,
    mean stuck length, relative spread of stuck length, mean slide steps per slide, max |x|)."""
    xs, slips = xs[-tail:], slips[-tail:]
    stuck, slides, cur, run = [], [], 0, 0
    for s in slips:
        if s == 0:
            if run:
                slides.append(run)
                run = 0
            cur += 1
        else:
            if cur:
                stuck.append(cur)
                cur = 0
            run += 1
    if not stuck:
        return 0, 0.0, 0.0, 0.0, max(abs(v) for v in xs)
    mean = sum(stuck) / len(stuck)
    sd = math.sqrt(sum((v - mean) ** 2 for v in stuck) / len(stuck))
    ms = sum(slides) / len(slides) if slides else 0.0
    return len(stuck), mean, sd / mean, ms, max(abs(v) for v in xs)
