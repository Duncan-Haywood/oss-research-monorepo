"""Stylised model: a planar 3R arm assembling a copy of its own printed gripper.

Everything here is a chosen number for this study. None of it is measured from a real arm
(the dimensions are of the order of low-cost desktop arms but are not the SO-101's).
Units: metres, kilograms, newtons, degrees.
"""
import math
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Arm:
    l1: float = 0.20
    l2: float = 0.20
    l3: float = 0.10                 # wrist to fingertip centre
    base_x: float = 0.0              # base position along the table (x), height z=0.10 above table
    base_z: float = 0.10
    q1: tuple = (-10.0, 190.0)       # shoulder limits (deg)
    q2: tuple = (-150.0, 150.0)      # elbow limits (relative, deg)
    pitch_tol: float = 15.0          # tool pitch may differ from the wanted pitch by this much
    payload: float = 0.15            # kg at the fingertips
    push: float = 12.0               # N the tool can push along its axis
    opening: float = 0.060           # gripper opening (m)


def ik_2r(arm, x, z):
    """Both elbow solutions (q1, q2) in degrees for a wrist point (x, z) relative to the base."""
    r2 = x * x + z * z
    c2 = (r2 - arm.l1 ** 2 - arm.l2 ** 2) / (2 * arm.l1 * arm.l2)
    if abs(c2) > 1.0:
        return []
    out = []
    for s in (1.0, -1.0):
        q2 = math.atan2(s * math.sqrt(1 - c2 * c2), c2)
        q1 = math.atan2(z, x) - math.atan2(arm.l2 * math.sin(q2), arm.l1 + arm.l2 * math.cos(q2))
        out.append((math.degrees(q1), math.degrees(q2)))
    return out


def reachable(arm, x, z, pitch):
    """Can the fingertip centre reach table-frame point (x, z) with tool pitch within tolerance?

    pitch is the wanted direction of the tool axis in the x-z plane (-90 = pointing down, 0 = along +x).
    The pitch is searched in steps of 1 degree over the tolerance band.
    """
    px, pz = x - arm.base_x, z - arm.base_z
    p = -int(arm.pitch_tol)
    while p <= int(arm.pitch_tol):
        ph = math.radians(pitch + p)
        wx, wz = px - arm.l3 * math.cos(ph), pz - arm.l3 * math.sin(ph)
        for q1, q2 in ik_2r(arm, wx, wz):
            if q1 < -170.0:
                q1 += 360.0
            if arm.q1[0] <= q1 <= arm.q1[1] and arm.q2[0] <= q2 <= arm.q2[1]:
                return True
        p += 1
    return False


@dataclass(frozen=True)
class Part:
    name: str
    mass: float                      # kg
    grasp: float                     # width the gripper must open to hold it (m)
    pick: tuple                      # (x, z) on the part tray, fingertip position
    place: tuple                     # (x, z) fingertip position at the mounting site
    pitch: float                     # tool pitch for pick and place (-90 down, 0 horizontal)
    parent: str                      # part it mounts on ("" = fixture)
    join: str                        # "slide", "snap", "press", "screw"
    force: float                     # insertion force needed (N); screws need a driver
    printed: bool = True


JOINS_NEEDING_TOOL = {"screw"}


def gripper_parts(scale=1.0, screwless=False):
    """The gripper to be copied: a palm, two fingers, a rack, a cover, two guide pins, plus vitamins.

    scale multiplies the printed-part widths (a bigger gripper needs a wider opening).
    """
    s = scale
    parts = [
        Part("palm",     0.060, 0.050 * s, (0.30, 0.00), (0.40, 0.02), -90, "",       "slide",  0.0),
        Part("rack",     0.015, 0.012 * s, (0.33, 0.00), (0.40, 0.04), -90, "palm",   "slide",  3.0),
        Part("finger_l", 0.020, 0.018 * s, (0.36, 0.00), (0.37, 0.05), -90, "rack",   "snap",   8.0),
        Part("finger_r", 0.020, 0.018 * s, (0.39, 0.00), (0.43, 0.05), -90, "rack",   "snap",   8.0),
        Part("pin_a",    0.004, 0.006 * s, (0.42, 0.00), (0.38, 0.03), -90, "palm",   "press", 14.0),
        Part("pin_b",    0.004, 0.006 * s, (0.44, 0.00), (0.42, 0.03), -90, "palm",   "press", 14.0),
        Part("cover",    0.030, 0.045 * s, (0.46, 0.00), (0.40, 0.07), -90, "palm",   "snap",  16.0),
        Part("side_cap", 0.008, 0.020 * s, (0.48, 0.00), (0.47, 0.04),   0, "palm",   "snap",   9.0),
        Part("servo",    0.055, 0.023 * s, (0.50, 0.00), (0.40, 0.05), -90, "palm",   "screw",  0.0, False),
        Part("screw_1",  0.001, 0.004 * s, (0.52, 0.00), (0.38, 0.06), -90, "servo",  "screw",  0.0, False),
        Part("screw_2",  0.001, 0.004 * s, (0.53, 0.00), (0.42, 0.06), -90, "servo",  "screw",  0.0, False),
    ]
    if screwless:
        # redesign for the arm: the servo clips into the palm and the two screws are dropped
        parts = [p for p in parts if not p.name.startswith("screw_")]
        parts = [replace(p, join="snap", force=10.0) if p.name == "servo" else p for p in parts]
    return parts


def step_check(arm, part):
    """Return the list of reasons the arm cannot do this step (empty list = feasible)."""
    why = []
    if part.grasp > arm.opening:
        why.append("grasp wider than opening")
    if part.mass > arm.payload:
        why.append("over payload")
    if not reachable(arm, part.pick[0], part.pick[1], part.pitch):
        why.append("pick unreachable")
    if not reachable(arm, part.place[0], part.place[1], part.pitch):
        why.append("place unreachable")
    if part.join in JOINS_NEEDING_TOOL:
        why.append("needs a screwdriver")
    elif part.force > arm.push:
        why.append("insertion force over push limit")
    return why


def assemble(arm, parts, assemble_vitamins=False):
    """Greedy closure: a part is assembled if its step is feasible and its parent is assembled.

    Only printed parts count towards the copy unless assemble_vitamins is set (the arm cannot
    make a servo or a screw either way; this only asks whether it could place them).
    Returns (done, blocked) where blocked maps a part name to its reasons.
    """
    done, blocked = [], {}
    names = {p.name for p in parts}
    changed = True
    remaining = list(parts)
    while changed:
        changed = False
        for p in list(remaining):
            if p.parent and p.parent not in done:
                continue
            why = step_check(arm, p)
            if why:
                blocked[p.name] = why
                remaining.remove(p)
                continue
            done.append(p.name)
            remaining.remove(p)
            changed = True
    for p in remaining:
        blocked.setdefault(p.name, ["parent not assembled: " + p.parent])
    assert set(done) | set(blocked) == names
    return done, blocked


def fractions(parts, done):
    printed = [p for p in parts if p.printed]
    d = set(done)
    n = sum(1 for p in printed if p.name in d) / len(printed)
    m = sum(p.mass for p in printed if p.name in d) / sum(p.mass for p in printed)
    allm = sum(p.mass for p in parts if p.name in d) / sum(p.mass for p in parts)
    return n, m, allm
