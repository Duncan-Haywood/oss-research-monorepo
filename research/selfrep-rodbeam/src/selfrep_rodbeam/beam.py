"""Euler-Bernoulli check of replacing the Prusa Mendel's 8 mm steel smooth rods by wood or printed rods.

Model: a rod of length L, simply supported at both ends, carrying a point load P at midspan (the carriage).
Deflection = P L^3 / (48 E I), I = pi d^4 / 64. Everything numeric below (loads, moduli, density, tolerance)
is an ASSUMPTION of this project; see the README. Shear deformation, creep, wood humidity, rod end fixity
and the carriage's own tilt are not modelled.
"""
import math

E_STEEL = 200e9          # Pa, textbook value for carbon steel
D0 = 8e-3                # m, the Mendel's smooth-rod diameter
DENSITY = {"steel": 7850.0, "wood": 700.0, "pla": 1240.0}   # kg/m3, assumed round values


def inertia(d):
    return math.pi * d ** 4 / 64.0


def deflection(P, L, E, d):
    return P * L ** 3 / (48.0 * E * inertia(d))


def matched_diameter(E, d0=D0, E0=E_STEEL):
    """Diameter giving the same midspan deflection as the d0 rod of modulus E0: d = d0 (E0/E)^(1/4)."""
    return d0 * (E0 / E) ** 0.25


def tolerance_diameter(P, L, E, tol):
    """Smallest diameter whose midspan deflection is <= tol."""
    return (P * L ** 3 * 64.0 / (48.0 * E * math.pi * tol)) ** 0.25


def rod_mass_g(material, L, d):
    return DENSITY[material] * math.pi * d ** 2 / 4.0 * L * 1e3
