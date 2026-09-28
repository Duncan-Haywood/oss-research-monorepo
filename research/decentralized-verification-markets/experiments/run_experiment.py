#!/usr/bin/env python3
"""Run the decentralized-training-verification simulation and print a
results report: incentive compatibility, aggregate accuracy, manipulation
vulnerability vs. the Credibly Neutral AI Oracles eps(1-eps) bound, and
audit-cost savings vs. a Verde-style "recompute everything" baseline.

Usage:
    python experiments/run_experiment.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from verification_markets.metrics import (  # noqa: E402
    audit_cost_savings,
    average_payoff_by_strategy,
    incentive_compatibility_gap,
    majority_vote_error_rate,
    market_brier_score,
    non_honest_fraction,
    theoretical_manipulation_bound,
)
from verification_markets.simulation import SimulationConfig, run_simulation  # noqa: E402


def print_header(title: str) -> None:
    print()
    print(title)
    print("=" * len(title))


def main() -> None:
    base_config = SimulationConfig(
        n_tasks=2000,
        corruption_rate=0.15,
        signal_noise=0.1,
        n_honest=14,
        n_lazy=3,
        n_colluding=3,
        n_adversarial=2,
        market_liquidity=5.0,
        audit_fraction=0.05,
        seed=42,
    )
    result = run_simulation(base_config)

    print_header("Incentive compatibility (avg. payoff by strategy)")
    for mechanism_name, payoff in (("Peer Truth Serum", result.pts_payoff),
                                    ("Correlated Agreement", result.ca_payoff)):
        by_strategy = average_payoff_by_strategy(result, payoff)
        gap = incentive_compatibility_gap(by_strategy)
        print(f"\n{mechanism_name}:")
        for strategy, payoff_value in sorted(by_strategy.items()):
            print(f"  {strategy:>12}: {payoff_value:+.4f}")
        verdict = "OK, incentive-compatible" if gap > 0 else "NEGATIVE -- see README §Limitations"
        print(f"  honest advantage over best deviation: {gap:+.4f} ({verdict})")

    print_header("Aggregate accuracy")
    print(f"LMSR market Brier score (0=perfect, 0.25=uninformed): "
          f"{market_brier_score(result):.4f}")
    print(f"Majority-vote error rate: {majority_vote_error_rate(result):.4f}")

    print_header("Audit cost savings vs. full recomputation (Verde baseline)")
    print(f"Fraction of tasks NOT requiring ground-truth recomputation: "
          f"{audit_cost_savings(result):.1%}")

    print_header("Manipulation vulnerability sweep "
                  "(empirical majority-vote error vs. Credibly Neutral AI Oracles' eps(1-eps) bound)")
    print(f"{'non-honest frac (eps)':>24} | {'empirical error':>16} | {'eps*(1-eps) bound':>18}")
    print("-" * 64)
    sweep_points = [
        dict(n_honest=19, n_lazy=1, n_colluding=0, n_adversarial=0),
        dict(n_honest=16, n_lazy=2, n_colluding=1, n_adversarial=1),
        dict(n_honest=12, n_lazy=3, n_colluding=3, n_adversarial=2),
        dict(n_honest=8, n_lazy=4, n_colluding=4, n_adversarial=4),
        dict(n_honest=4, n_lazy=5, n_colluding=5, n_adversarial=6),
    ]
    for point in sweep_points:
        config = SimulationConfig(
            n_tasks=1200,
            corruption_rate=0.2,
            signal_noise=0.1,
            market_liquidity=5.0,
            seed=99,
            **point,
        )
        sweep_result = run_simulation(config)
        eps = non_honest_fraction(sweep_result)
        empirical_err = majority_vote_error_rate(sweep_result)
        bound = theoretical_manipulation_bound(eps)
        print(f"{eps:>24.2f} | {empirical_err:>16.4f} | {bound:>18.4f}")


if __name__ == "__main__":
    main()
