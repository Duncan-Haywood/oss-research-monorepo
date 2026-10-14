"""Euler-Bernoulli beam model of a RepRap-class smooth rod (stylised).

All material moduli, loads and the deflection limit are ASSUMPTIONS, given as
ranges; see README. Units: SI (m, N, Pa) unless a name says otherwise.
"""
import math
import random

G = 9.81
# (low, nominal, high) Young's modulus in Pa. Assumed typical ranges, not measurements.
MATERIALS = {
    "steel": (190e9, 200e9, 210e9),
    "birch_dowel": (9e9, 12e9, 15e9),      # along the grain, assumed
    "pla_printed": (1.5e9, 2.5e9, 3.5e9),  # printed part, assumed
}


def inertia_solid(d):
    return math.pi * d ** 4 / 64.0


def inertia_tube(d_out, d_in):
    return math.pi * (d_out ** 4 - d_in ** 4) / 64.0


def deflection(E, I, length, load_n, support="simply"):
    """Mid-span deflection of a beam under a central point load.

    simply supported: F L^3 / (48 E I); both ends clamped: F L^3 / (192 E I).
    """
    k = {"simply": 48.0, "clamped": 192.0}[support]
    return load_n * length ** 3 / (k * E * I)


def self_weight_deflection(E, I, length, rho, area, support="simply"):
    """Mid-span deflection under the rod's own weight (uniform load)."""
    w = rho * area * G
    k = {"simply": 384.0 / 5.0, "clamped": 384.0}[support]
    return w * length ** 4 / (k * E * I)


def equal_stiffness_diameter(E, E_ref, d_ref):
    """Solid-rod diameter with the same bending stiffness EI as the reference."""
    return d_ref * (E_ref / E) ** 0.25


def passes(E, d, length, load_n, limit, support="simply"):
    return deflection(E, inertia_solid(d), length, load_n, support) <= limit


def pass_probability(material, d, length, load_n, limit, support="simply",
                     draws=2000, seed=0):
    """Share of draws, E uniform on the assumed range, whose deflection is within limit."""
    lo, _, hi = MATERIALS[material]
    rng = random.Random(seed)
    ok = sum(passes(rng.uniform(lo, hi), d, length, load_n, limit, support)
             for _ in range(draws))
    return ok / draws


def min_passing_diameter(E, length, load_n, limit, support="simply"):
    """Smallest solid diameter whose mid-span deflection is within limit."""
    # delta = F L^3 / (k E pi d^4/64)  =>  d = (64 F L^3 / (k E pi limit))^(1/4)
    k = {"simply": 48.0, "clamped": 192.0}[support]
    return (64.0 * load_n * length ** 3 / (k * E * math.pi * limit)) ** 0.25
