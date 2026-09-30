"""Sample twin.  Real plant: unit mass x'' = u, PD control u = -kp x_k - kd v_k sampled every T and held (zero-order hold).
Twin: continuous-time control, closed loop s^2 + kd s + kp, stable for every kp, kd > 0.
Exact ZOH discretisation, state (x, v):  x+ = x + T v + T^2/2 u,  v+ = v + T u.  Closed loop
    trace = 2 - kp T^2/2 - kd T,   det = 1 - kd T + kp T^2/2,
and the Jury conditions reduce to  det < 1  (kd > kp T/2),  1+det-trace = kp T^2 > 0,  1+det+trace = 4 - 2 kd T > 0 (kd < 2/T).
So the real loop is stable iff  kp T/2 < kd < 2/T.  With kp = wn^2, kd = 2 zeta wn, eps = wn T:  eps < min(4 zeta, 1/zeta).
"""
import cmath
import math


def gains(wn, zeta):
    return wn * wn, 2.0 * zeta * wn


def trace_det(kp, kd, T):
    return 2.0 - kp * T * T / 2.0 - kd * T, 1.0 - kd * T + kp * T * T / 2.0


def multipliers(kp, kd, T):
    """Closed-loop multipliers: roots of z^2 - trace z + det."""
    tr, dt = trace_det(kp, kd, T)
    d = cmath.sqrt(tr * tr - 4.0 * dt)
    return (tr + d) / 2.0, (tr - d) / 2.0


def spectral_radius(kp, kd, T):
    return max(abs(z) for z in multipliers(kp, kd, T))


def real_stable(kp, kd, T):
    """Exact stability of the sampled loop."""
    return kp > 0 and kd > kp * T / 2.0 and kd * T < 2.0


def eps_limit(zeta):
    """Largest eps = wn T with a stable sampled loop at damping ratio zeta: min(4 zeta, 1/zeta)."""
    return min(4.0 * zeta, 1.0 / zeta)


def mechanism(zeta):
    """'delay' (det -> 1, complex pair on the unit circle) for zeta < 1/2, 'derivative' (multiplier -> -1) for zeta > 1/2."""
    return "delay" if zeta < 0.5 else "derivative" if zeta > 0.5 else "both"


def hunt_angle(eps):
    """Argument of the unit-circle pair at the delay boundary kd = kp T/2: cos(theta) = 1 - eps^2/2, theta = 2 asin(eps/2)."""
    return 2.0 * math.asin(eps / 2.0)


def deadbeat_gains(T):
    """Both multipliers at 0: kp = 1/T^2, kd = 3/(2T)  (eps = 1, zeta = 3/4)."""
    return 1.0 / (T * T), 1.5 / T


def step(kp, kd, T, x0, n):
    """Exact sampled response from (x0, 0): list of x_k, k = 1..n."""
    a = 1.0 - kp * T * T / 2.0
    b = T - kd * T * T / 2.0
    c = -kp * T
    d = 1.0 - kd * T
    x, v = x0, 0.0
    out = []
    for _ in range(n):
        x, v = a * x + b * v, c * x + d * v
        out.append(x)
    return out


def step_rk4(kp, kd, T, x0, n, sub=200):
    """Independent check of the discretisation: RK4 of the continuous plant with the command held constant over each period."""
    h = T / sub
    x, v = x0, 0.0
    out = []
    for _ in range(n):
        u = -kp * x - kd * v
        for _ in range(sub):
            k1x, k1v = v, u
            k2x, k2v = v + h / 2 * k1v, u
            k3x, k3v = v + h / 2 * k2v, u
            k4x, k4v = v + h * k3v, u
            x += h / 6 * (k1x + 2 * k2x + 2 * k3x + k4x)
            v += h / 6 * (k1v + 2 * k2v + 2 * k3v + k4v)
        out.append(x)
    return out


def twin_step(wn, zeta, T, x0, n):
    """Continuous twin x(t) = closed-form 2nd-order step response sampled at t = T, 2T, ... (zeta != 1)."""
    out = []
    if zeta < 1:
        wd = wn * math.sqrt(1 - zeta * zeta)
        for k in range(1, n + 1):
            t = k * T
            out.append(x0 * math.exp(-zeta * wn * t) * (math.cos(wd * t) + zeta * wn / wd * math.sin(wd * t)))
    elif zeta > 1:
        r = wn * math.sqrt(zeta * zeta - 1)
        s1, s2 = -zeta * wn + r, -zeta * wn - r
        for k in range(1, n + 1):
            t = k * T
            out.append(x0 * (s1 * math.exp(s2 * t) - s2 * math.exp(s1 * t)) / (s1 - s2))
    else:
        for k in range(1, n + 1):
            t = k * T
            out.append(x0 * math.exp(-wn * t) * (1 + wn * t))
    return out


def twin_overshoot(zeta):
    return math.exp(-math.pi * zeta / math.sqrt(1 - zeta * zeta)) if zeta < 1 else 0.0


def overshoot(xs, x0):
    """Largest excursion to the far side of the target, as a fraction of |x0|."""
    return max(0.0, max(-x * (1 if x0 > 0 else -1) for x in xs) / abs(x0))
