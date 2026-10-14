"""Bounds for an infrared-gating textile, using garment-twonodeoptics' switchable two-node model.
The model itself lives in ../garment-twonodeoptics; this module only fixes the two gate states."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "garment-twonodeoptics", "src"))
from garment_twonodeoptics import flex  # noqa: E402

OURS, REF = flex.OURS, flex.REF
CLOSED, OPEN = 0.15, 0.8          # infrared transmittance bounds taken from garment-thermal section E
HOURS3, STEADY = 180, 1440


def bounds(room_t, opts, minutes, met=1.2, clo=0.5, rh=50, v=0.1):
    """(closed, open) end states in a still room with air = radiant temperature room_t."""
    return tuple(flex.run(met, clo, room_t, rh, v=v, opts=opts, tr=room_t, tau=t, minutes=minutes)
                 for t in (CLOSED, OPEN))
