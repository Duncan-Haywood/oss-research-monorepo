import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from garment_twonodegate import gate

OPTS = [gate.OURS, gate.REF]

@pytest.mark.parametrize("opts", OPTS)
@pytest.mark.parametrize("room", [31, 16])
def test_opening_gate_cools_skin(room, opts):
    closed, open_ = gate.bounds(room, opts, gate.HOURS3)
    assert open_["tsk"] < closed["tsk"]

@pytest.mark.parametrize("opts", OPTS)
def test_hot_room_open_lowers_evaporation(opts):
    closed, open_ = gate.bounds(31, opts, gate.HOURS3)
    assert open_["evap"] < closed["evap"] and open_["wet"] < closed["wet"]

@pytest.mark.parametrize("opts", OPTS)
@pytest.mark.parametrize("room", [31, 16])
def test_steady_state_reached(room, opts):
    a = gate.bounds(room, opts, gate.STEADY)
    b = gate.bounds(room, opts, 2 * gate.STEADY)
    for x, y in zip(a, b):
        assert max(abs(x[k] - y[k]) for k in ("tsk", "tcr", "dry", "evap")) < 0.01

def test_gate_effect_on_skin_is_choice_robust():
    d = []
    for o in OPTS:
        c, op = gate.bounds(16, o, gate.STEADY)
        d.append(op["tsk"] - c["tsk"])
    assert abs(d[0] - d[1]) < 0.1
