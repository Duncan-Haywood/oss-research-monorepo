"""Peer-prediction mechanisms: elicit honest reports about a hidden state
using only *other agents' reports* as the scoring reference, with no access
to ground truth.

Implements two mechanisms from the peer-prediction literature, specialized
to binary reports (e.g. "this training step's gradient update was computed
correctly" vs. not):

- Peer Truth Serum (PTS): Faltings, Jurca, Pu & Tran (2014); Radanovic,
  Faltings & Jurca (2016) (PTSC, the multi-task version with an empirical
  prior); see also Faltings & Radanovic, "Game Theory for Data Science:
  Eliciting Truthful Information" (2017). Pays agent i by comparing to a
  single reference peer j, scaled by the (empirical) population report
  frequency, so that truthful reporting is an equilibrium under the belief
  conditions given in those papers, while any *uninformative* fixed/random
  strategy earns expected payment ~0.

- Correlated Agreement (CA): Shnayder, Agarwal, Frongillo & Parkes (2016),
  "Informed Truthfulness in Multi-Task Peer Prediction", generalising the
  binary-signal mechanism of Dasgupta & Ghosh (2013). The ``ca_payment``
  used by the simulation is a deliberately *simplified* variant: it
  estimates the delta matrix ``P_same(x, y) - P_diff(x, y)`` by pooling
  every agent's reports (including deviators'), and pays ``delta[r_i, r_j]``
  on the shared task only. CA as specified pays ``S(r_i, r_j)`` on a bonus
  task *minus* ``S`` on a pair of reports from two unrelated (penalty)
  tasks, with ``S = 1[delta > 0]``; the penalty term makes any
  signal-independent strategy earn 0 in expectation.

  Dropping the penalty term is what breaks the simplified variant: with
  ``delta[(1, 1)] > 0``, an agent that always reports 1 collects a positive
  payment on every task, and under a skewed base rate this can out-earn
  honest reporting (tests/test_simulation.py::test_ca_is_vulnerable_to_simultaneous_correlated_deviation).
  ``ca_penalty_payoffs`` implements the penalty-term payment rule on the
  same pooled delta estimate; in the same populations it keeps honest
  reporting ahead (test_ca_with_penalty_term_resists_the_same_deviation),
  so the failure belongs to this simplification, not to CA. Peer Truth
  Serum avoids it differently: dividing by the peer's marginal report
  probability cancels the "always guess the popular answer" exploit.
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Dict, Iterable, List, Tuple

_EPS = 1e-9


def _clip(p: float) -> float:
    return min(max(p, _EPS), 1 - _EPS)


def peer_truth_serum(report_i: int, report_peer: int, prior_prob_one: float) -> float:
    """Peer Truth Serum payment for report_i, scored against a single peer.

    Args:
        report_i: agent i's binary report (0 or 1).
        report_peer: a randomly selected peer's binary report.
        prior_prob_one: the common-knowledge (or empirically estimated)
            population probability that a report equals 1.

    Returns:
        The PTS payment. Truthful reporting is a strict Bayes-Nash
        equilibrium (given a "stochastically relevant" signal structure);
        any fixed/uninformative reporting strategy has expected payment 0.
    """
    prior_prob_one = _clip(prior_prob_one)
    peer_prob = prior_prob_one if report_peer == 1 else (1 - prior_prob_one)
    match = 1.0 if report_i == report_peer else 0.0
    return match / peer_prob - 1.0


def correlated_agreement_matrix(
    reports_by_agent: Dict[int, Dict[int, int]],
    rng: random.Random,
    n_shuffles: int = 200,
) -> Dict[Tuple[int, int], float]:
    """Estimate the CA "delta" matrix Delta[x][y] = P_same(x,y) - P_diff(x,y).

    Args:
        reports_by_agent: {agent_id: {task_id: report}}.
        rng: random.Random instance for the cross-task shuffle baseline.
        n_shuffles: number of random cross-task pairings used to estimate
            the "different task" baseline distribution.

    Returns:
        A dict mapping (x, y) in {0,1}x{0,1} to Delta[x][y].
    """
    agents = list(reports_by_agent)
    same_counts: Dict[Tuple[int, int], int] = defaultdict(int)
    same_total = 0
    for a_idx, agent_a in enumerate(agents):
        for agent_b in agents[a_idx + 1 :]:
            shared_tasks = set(reports_by_agent[agent_a]) & set(reports_by_agent[agent_b])
            for t in shared_tasks:
                x = reports_by_agent[agent_a][t]
                y = reports_by_agent[agent_b][t]
                same_counts[(x, y)] += 1
                same_total += 1

    diff_counts: Dict[Tuple[int, int], int] = defaultdict(int)
    diff_total = 0
    for a_idx, agent_a in enumerate(agents):
        tasks_a = list(reports_by_agent[agent_a])
        for agent_b in agents[a_idx + 1 :]:
            tasks_b = list(reports_by_agent[agent_b])
            if not tasks_a or not tasks_b:
                continue
            for _ in range(n_shuffles):
                t_a = rng.choice(tasks_a)
                t_b = rng.choice(tasks_b)
                if t_a == t_b:
                    continue
                x = reports_by_agent[agent_a][t_a]
                y = reports_by_agent[agent_b][t_b]
                diff_counts[(x, y)] += 1
                diff_total += 1

    delta: Dict[Tuple[int, int], float] = {}
    for x in (0, 1):
        for y in (0, 1):
            p_same = same_counts[(x, y)] / same_total if same_total else 0.0
            p_diff = diff_counts[(x, y)] / diff_total if diff_total else 0.0
            delta[(x, y)] = p_same - p_diff
    return delta


def ca_payment(report_i: int, report_peer: int, delta: Dict[Tuple[int, int], float]) -> float:
    """Correlated Agreement payment: reward reports whose pairwise pattern
    with a peer is more common on shared tasks than on random cross-task
    pairings, i.e. Delta[report_i][report_peer]."""
    return delta.get((report_i, report_peer), 0.0)


def ca_penalty_payoffs(
    reports_by_agent: Dict[int, Dict[int, int]],
    delta: Dict[Tuple[int, int], float],
    rng: random.Random,
) -> Dict[int, float]:
    """Total CA payoff per agent under the payment rule of Shnayder, Agarwal,
    Frongillo & Parkes (2016), for comparison with the simplified
    ``ca_payment`` above.

    For each agent ``i`` and each (bonus) task ``t``: pick a random peer
    ``j`` and two distinct penalty tasks ``t1 != t2``, both different from
    ``t``; pay ``S(r_i[t], r_j[t]) - S(r_i[t1], r_j[t2])`` with
    ``S(x, y) = 1 if delta[(x, y)] > 0 else 0``. The penalty term is what
    ``ca_payment`` leaves out: a report that ignores the signal (e.g. always
    1) has the same expected score on the bonus and penalty pairs, so it
    earns 0 in expectation whatever the other agents do. Assumes every agent
    reports on the same tasks (as in ``simulation.py``) and at least 3 tasks.
    """
    agents = list(reports_by_agent)
    tasks = sorted(reports_by_agent[agents[0]])
    score = {k: (1.0 if v > 0 else 0.0) for k, v in delta.items()}
    out = {i: 0.0 for i in agents}
    for t in tasks:
        for i in agents:
            j = rng.choice([a for a in agents if a != i])
            t1 = t2 = t
            while t1 == t:
                t1 = rng.choice(tasks)
            while t2 in (t, t1):
                t2 = rng.choice(tasks)
            out[i] += score.get((reports_by_agent[i][t], reports_by_agent[j][t]), 0.0) - score.get(
                (reports_by_agent[i][t1], reports_by_agent[j][t2]), 0.0
            )
    return out


def empirical_prior(reports: Iterable[int]) -> float:
    reports = list(reports)
    if not reports:
        return 0.5
    return sum(reports) / len(reports)
