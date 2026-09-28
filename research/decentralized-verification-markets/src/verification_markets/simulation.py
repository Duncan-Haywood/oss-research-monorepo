"""Simulation harness: a population of verifiers reports on a stream of
synthetic decentralized-ML-training "tasks" (steps that are either computed
correctly or are faulty/fraudulent), and three mechanisms price / aggregate
those reports:

1. Peer Truth Serum (PTS) payments per verifier.
2. Correlated Agreement (CA) payments per verifier.
3. An LMSR market maker that aggregates all reports on a task into a single
   calibrated probability of correctness.

The goal is to measure, without ever using ground truth to pay verifiers
(ground truth is only used for audit-cost accounting and for evaluating
mechanism quality after the fact):

- Incentive compatibility: does the "honest" strategy earn a higher average
  payoff than "lazy", "colluding", or "adversarial" strategies?
- Aggregate accuracy: how well does the LMSR price (or a majority vote of
  reports) track ground truth?
- Cost savings vs. Verde-style "recompute everything": how much of the task
  stream needs true ground-truth auditing if peer prediction handles the
  rest?
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List

from .agents import Verifier, generate_tasks
from .market_maker import LMSRMarketMaker
from .peer_prediction import (
    ca_payment,
    correlated_agreement_matrix,
    empirical_prior,
    peer_truth_serum,
)


@dataclass
class SimulationConfig:
    n_tasks: int = 400
    corruption_rate: float = 0.15
    signal_noise: float = 0.1
    n_honest: int = 12
    n_lazy: int = 3
    n_colluding: int = 3
    n_adversarial: int = 2
    market_liquidity: float = 5.0
    market_trade_size: float = 1.0
    audit_fraction: float = 0.05
    seed: int = 0


@dataclass
class SimulationResult:
    config: SimulationConfig
    verifiers: List[Verifier]
    ground_truth: List[int]
    reports: Dict[int, Dict[int, int]]  # {verifier_id: {task_id: report}}
    pts_payoff: Dict[int, float]
    ca_payoff: Dict[int, float]
    market_price: List[float]  # per task, price_yes after all reports traded
    audited_tasks: List[int] = field(default_factory=list)


def _build_verifiers(config: SimulationConfig) -> List[Verifier]:
    verifiers: List[Verifier] = []
    vid = 0
    for _ in range(config.n_honest):
        verifiers.append(Verifier(vid, "honest", config.signal_noise))
        vid += 1
    for _ in range(config.n_lazy):
        verifiers.append(Verifier(vid, "lazy", config.signal_noise))
        vid += 1
    for _ in range(config.n_colluding):
        verifiers.append(Verifier(vid, "colluding", config.signal_noise))
        vid += 1
    for _ in range(config.n_adversarial):
        verifiers.append(Verifier(vid, "adversarial", config.signal_noise))
        vid += 1
    return verifiers


def run_simulation(config: SimulationConfig) -> SimulationResult:
    rng = random.Random(config.seed)
    verifiers = _build_verifiers(config)
    ground_truth = generate_tasks(config.n_tasks, config.corruption_rate, rng)

    # Each verifier reports on every task.
    reports: Dict[int, Dict[int, int]] = {v.id: {} for v in verifiers}
    for t, truth in enumerate(ground_truth):
        for v in verifiers:
            reports[v.id][t] = v.report(truth, rng)

    all_reports_flat = [r for by_task in reports.values() for r in by_task.values()]
    global_prior = empirical_prior(all_reports_flat)

    # Peer Truth Serum: pay each verifier against one random peer per task.
    pts_payoff: Dict[int, float] = {v.id: 0.0 for v in verifiers}
    for t in range(config.n_tasks):
        reporters = [v for v in verifiers]
        for v in reporters:
            peers = [p for p in reporters if p.id != v.id]
            if not peers:
                continue
            peer = rng.choice(peers)
            pts_payoff[v.id] += peer_truth_serum(
                reports[v.id][t], reports[peer.id][t], global_prior
            )

    # Correlated Agreement: build the delta matrix from the full report
    # history, then pay each verifier against one random peer per task.
    delta = correlated_agreement_matrix(reports, rng)
    ca_payoff: Dict[int, float] = {v.id: 0.0 for v in verifiers}
    for t in range(config.n_tasks):
        reporters = [v for v in verifiers]
        for v in reporters:
            peers = [p for p in reporters if p.id != v.id]
            if not peers:
                continue
            peer = rng.choice(peers)
            ca_payoff[v.id] += ca_payment(reports[v.id][t], reports[peer.id][t], delta)

    # LMSR aggregation: one fresh market per task, verifiers trade in a
    # random order, final price is the aggregate probability the step was
    # computed correctly.
    market_price: List[float] = []
    for t in range(config.n_tasks):
        market = LMSRMarketMaker(liquidity=config.market_liquidity)
        order = list(verifiers)
        rng.shuffle(order)
        for v in order:
            market.trade(reports[v.id][t], config.market_trade_size)
        market_price.append(market.price_yes())

    n_audited = max(1, int(round(config.n_tasks * config.audit_fraction)))
    audited_tasks = rng.sample(range(config.n_tasks), k=min(n_audited, config.n_tasks))

    return SimulationResult(
        config=config,
        verifiers=verifiers,
        ground_truth=ground_truth,
        reports=reports,
        pts_payoff=pts_payoff,
        ca_payoff=ca_payoff,
        market_price=market_price,
        audited_tasks=audited_tasks,
    )
