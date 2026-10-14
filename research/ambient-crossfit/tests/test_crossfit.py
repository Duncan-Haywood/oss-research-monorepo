import numpy as np

from ambient_crossfit.core import CAPS, FIT_NAMES, PRIOR_W, World, crossfit_m, dr_labels_m, fit_map, ips_value, run_logged, sigmoid, simulate


def test_all_fits_returned_and_finite():
    w = World(); d = simulate(w, 20, np.random.default_rng(2))
    fits, info = run_logged(w, d, np.random.default_rng(3), eps=0.02, hours=(20,))
    assert set(fits[20]) == set(FIT_NAMES) and info[20]["nlab"] > 0
    assert info[20]["cap"] in CAPS and info[20]["cap_prior"] in CAPS
    assert all(np.all(np.isfinite(v)) for v in fits[20].values())


def test_eps_one_all_labelled_dr_equals_full_fit():
    w = World(); d = simulate(w, 10, np.random.default_rng(4))
    fits, info = run_logged(w, d, np.random.default_rng(5), eps=1.0, hours=(10,))
    for k in ("biased", "clip10", "dr_plain", "dr_cf", "random_matched", "full"):
        assert np.allclose(fits[10][k], fits[10]["full"], atol=1e-8), k   # S=1, pi=1 -> pseudo-label is y


def test_crossfit_predictions_are_out_of_fold():
    w = World(); d = simulate(w, 10, np.random.default_rng(6))
    X, y = d["X"], d["need"].astype(float)
    spoke = np.ones(len(y), bool); prop = np.ones(len(y))
    m, fold = crossfit_m(X, y, spoke, prop, PRIOR_W, 1.0, 2, np.random.default_rng(7))
    for k in range(2):
        wk, _ = fit_map(X[fold != k], y[fold != k], PRIOR_W, 1.0, np.ones((fold != k).sum()))
        assert np.allclose(m[fold == k], sigmoid(X[fold == k] @ wk))


def test_ips_value_matches_true_value_when_everything_logged():
    from ambient_crossfit.core import run_fixed
    w = World(); d = simulate(w, 30, np.random.default_rng(8))
    wt = np.array([1.0, 0.5, -0.5, -3.0]); n = len(d["need"])
    v = ips_value(w, wt, d["X"], d["others"], d["wake"], d["need"].astype(float), np.ones(n, bool), np.ones(n))
    assert np.isclose(v, run_fixed(w, d, wt).mean())


def test_dr_labels_are_y_where_spoke_with_unit_propensity():
    y = np.array([1.0, 0.0, 1.0]); m = np.array([0.3, 0.6, 0.1])
    out = dr_labels_m(y, np.array([True, True, False]), np.ones(3), m)
    assert np.allclose(out, [1.0, 0.0, 0.1])
