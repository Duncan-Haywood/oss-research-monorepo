import numpy as np
from ambient_dscorr.sim import Params, contexts
from ambient_dscorr.est import (PRIOR, confusion, joint_audit, joint_audit2, joint_audit2c, draw_audit2c,
                                estimate_naive, estimate_ds, u_table, policies)

P = Params()


def test_rho0_equals_independent_joint():
    C, A1, A2 = confusion(0.7), confusion(0.8), confusion(0.9)
    assert np.allclose(joint_audit2c(C, A1, A2, PRIOR, 0.0), joint_audit2(C, A1, A2, PRIOR))


def test_unequal_auditors_auditor2_marginal_is_a_mixture():
    C, A1, A2 = confusion(0.7), confusion(0.9), confusion(0.7)
    J = joint_audit2c(C, A1, A2, PRIOR, 0.5)
    assert np.allclose(J.sum(axis=0), joint_audit(C, confusion(0.8), PRIOR))


def test_joint_sums_to_one_and_equal_auditor_marginals_unchanged():
    C, A1, A2 = confusion(0.7), confusion(0.8), confusion(0.8)
    for rho in (0.25, 0.5, 1.0):
        J = joint_audit2c(C, A1, A2, PRIOR, rho)
        assert np.isclose(J.sum(), 1.0)
        assert np.allclose(J.sum(axis=1), joint_audit(C, A1, PRIOR))          # auditor 1 with classifier
        assert np.allclose(J.sum(axis=0), joint_audit(C, A2, PRIOR))          # auditor 2 with classifier


def test_rho1_auditors_always_agree():
    J = joint_audit2c(confusion(0.7), confusion(0.8), confusion(0.8), PRIOR, 1.0)
    off = J.copy()
    for a in range(3):
        off[a, a, :] = 0
    assert off.sum() == 0


def test_sampler_matches_exact_joint():
    C, A1, A2 = confusion(0.7), confusion(0.8), confusion(0.7)
    c = draw_audit2c(C, A1, A2, PRIOR, 200000, 0.5, np.random.default_rng(1))
    assert c.sum() == 200000
    assert np.abs(c / c.sum() - joint_audit2c(C, A1, A2, PRIOR, 0.5)).max() < 4e-3


def test_ds_exact_when_independent_and_overconfident_when_shared():
    C, A1, A2 = confusion(0.7), confusion(0.8), confusion(0.8)
    _, C0, _, _ = estimate_ds(joint_audit2c(C, A1, A2, PRIOR, 0.0) * 1e9, iters=20000)
    assert np.abs(C0 - C).max() < 2e-3
    _, C5, h1, _ = estimate_ds(joint_audit2c(C, A1, A2, PRIOR, 0.5) * 1e9, iters=20000)
    assert np.diag(h1).mean() > 0.8 + 0.01            # auditor accuracy over-estimated
    assert np.abs(C5 - C).max() > 0.01                # classifier matrix no longer recovered


def test_no_estimate_beats_true_parameter_bayes():
    C, A1, A2 = confusion(0.7), confusion(0.8), confusion(0.8)
    counts = draw_audit2c(C, A1, A2, PRIOR, 200, 0.5, np.random.default_rng(3))
    pd, Cd, _, _ = estimate_ds(counts)
    pn, Cn = estimate_naive(counts.sum(axis=1), 1.0)
    for c in contexts()[:12]:
        r = policies(u_table(P, c), C, PRIOR, pn, Cn, pd, Cd)
        assert r["bayes_em"] <= r["bayes_true"] + 1e-12 and r["bayes_naive"] <= r["bayes_true"] + 1e-12
