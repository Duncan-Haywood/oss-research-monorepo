"""Sweep twin.  Real sensor: a spinning 2-D lidar that sweeps azimuth theta = w t over one scan period T (w = 2 pi / T) while the robot
moves with velocity v (and optionally yaw rate Om).  Twin: the whole scan is taken at one instant.
A wall n.x = d (unit normal n at sensor azimuth th0) is hit at time t = (th0 + delta)/w by the beam at offset delta from the normal; in
the sensor frame the hit is (along the wall, along the normal) = ((d - vn t) tan(delta), d - vn t), vn = n.v.  The normal coordinate is
exactly linear in t, so the wall is straight but rotated: to first order its normal is turned by psi = vn/(w d) = vn T/(2 pi d) and it is
offset by vn t0.  Only the velocity component normal to the wall matters.  A yaw rate Om bends the wall instead (curvature ~ Om/w).
"""
import math


def walls_rectangle(x0, x1, y0, y1):
    """Axis-aligned room; each wall is (unit normal pointing from the wall into the room's inward... as n.x = d in world coordinates)."""
    return [((1.0, 0.0), x1), ((-1.0, 0.0), -x0), ((0.0, 1.0), y1), ((0.0, -1.0), -y0)]


def cast(walls, p, heading, phi):
    """Range from point p along world azimuth heading+phi to the nearest wall (n.x = d, n outward)."""
    ux, uy = math.cos(heading + phi), math.sin(heading + phi)
    best = math.inf
    for (nx, ny), d in walls:
        den = nx * ux + ny * uy
        if den > 1e-12:
            r = (d - (nx * p[0] + ny * p[1])) / den
            if 0 < r < best:
                best = r
    return best


def scan(walls, v=(0.0, 0.0), yaw_rate=0.0, T=0.1, n_beams=1800, start=(0.0, 0.0), heading0=0.0, theta0=-0.75 * math.pi):
    """Points (x, y, t) in the sensor frame as recorded (as if at a single instant).  Beam k has azimuth theta0 + 2 pi k/n (theta0 = -3 pi/4 puts the scan seam on a room corner, away from the four walls) at time
    t = (theta - theta0)/w.  v = (0, 0) and yaw_rate = 0 is the twin."""
    w = 2 * math.pi / T
    pts = []
    for k in range(n_beams):
        th = theta0 + 2 * math.pi * k / n_beams
        t = (th - theta0) / w
        p = (start[0] + v[0] * t, start[1] + v[1] * t)
        r = cast(walls, p, heading0 + yaw_rate * t, th)
        pts.append((r * math.cos(th), r * math.sin(th), t))
    return pts


def sector(pts, center, half_width):
    """Points whose sensor azimuth is within half_width of center (radians)."""
    out = []
    for x, y, t in pts:
        a = math.atan2(y, x)
        d = (a - center + math.pi) % (2 * math.pi) - math.pi
        if abs(d) <= half_width:
            out.append((x, y, t))
    return out


def fit_line(pts):
    """Total-least-squares line n.x = d with unit normal n = (cos a, sin a) oriented away from the origin (d >= 0).  Returns (a, d)."""
    m = len(pts)
    mx = sum(p[0] for p in pts) / m
    my = sum(p[1] for p in pts) / m
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    syy = sum((p[1] - my) ** 2 for p in pts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    a = 0.5 * math.atan2(2 * sxy, sxx - syy) + math.pi / 2     # eigenvector of the smaller eigenvalue = normal direction
    d = mx * math.cos(a) + my * math.sin(a)
    if d < 0:
        a += math.pi
        d = -d
    return a % (2 * math.pi), d


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def wall_yaw(pts, center, half_width):
    """Apparent normal angle error (radians) and distance of the wall seen near sensor azimuth `center`."""
    a, d = fit_line(sector(pts, center, half_width))
    return wrap(a - center), d


def skew_formula(vn, T, d):
    """First-order apparent rotation of a wall at distance d, normal speed vn, scan period T."""
    return vn * T / (2 * math.pi * d)


def speed_limit(psi_tol, T, d):
    """Largest normal speed with apparent skew <= psi_tol: v* = 2 pi d psi_tol / T."""
    return 2 * math.pi * d * psi_tol / T


def deskew(pts, v_est):
    """Re-express each point in the start-of-scan frame assuming constant translation v_est (no rotation): p + v_est t."""
    return [(x + v_est[0] * t, y + v_est[1] * t, t) for x, y, t in pts]


def deskew_residual(vn, vn_est, T, d):
    """Skew left after deskewing with a normal-velocity estimate vn_est (first order): (vn - vn_est) T/(2 pi d)."""
    return skew_formula(vn - vn_est, T, d)


def deskew_tolerance(psi_tol, vn, T, d):
    """Largest relative velocity-estimate error eps = |vn - vn_est|/|vn| that keeps residual skew <= psi_tol."""
    return psi_tol / abs(skew_formula(vn, T, d))


def room_heading(pts, walls_nominal_azimuths, half_width):
    """Heading estimate from a room: circular mean of the (fitted - nominal) normal angles over the listed walls, weighted by point count.
    Returns (mean error, per-wall errors)."""
    errs, weights = [], []
    for c in walls_nominal_azimuths:
        s = sector(pts, c, half_width)
        a, _ = fit_line(s)
        errs.append(wrap(a - c))
        weights.append(len(s))
    return sum(e * w for e, w in zip(errs, weights)) / sum(weights), errs


def curvature_formula(yaw_rate, T, d):
    """Sagitta coefficient of the bent wall under yaw rate: h = d + kappa s^2/d with kappa = Om/w = Om T/(2 pi)."""
    return yaw_rate * T / (2 * math.pi)
