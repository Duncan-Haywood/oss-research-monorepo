"""Verifier agent models and synthetic training-step tasks.

Models the setting from Gensyn's Verde ("a verification system for machine
learning over untrusted nodes") and Credibly Neutral AI Oracles: a stream of
training steps, each of which was either computed correctly or is faulty /
fraudulent, and a population of verifiers who each get a noisy private
signal about correctness and must report it. Ground-truth recomputation
(the "referee" in Verde, the audited report layer in Credibly Neutral AI
Oracles) is expensive and only applied to a small audited subset; peer
prediction is used to price the other reports.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List


def generate_tasks(n_tasks: int, corruption_rate: float, rng: random.Random) -> List[int]:
    """Generate ground-truth correctness labels for `n_tasks` training steps.

    Each step is correct (1) with probability `1 - corruption_rate`, and
    faulty/fraudulent (0) otherwise.
    """
    return [0 if rng.random() < corruption_rate else 1 for _ in range(n_tasks)]


STRATEGIES = ("honest", "lazy", "colluding", "adversarial")


@dataclass
class Verifier:
    """A verifier agent with a fixed reporting strategy.

    Strategies:
        honest: observes a noisy private signal of ground truth and reports
            it truthfully.
        lazy: skips verification (no signal cost) and always reports the
            modal outcome ("correct"), free-riding on other verifiers.
        colluding: a coordinated block that always reports a fixed value
            ("correct") regardless of the true signal, attempting to
            whitewash faulty steps cheaply.
        adversarial: observes the true signal but reports its negation,
            actively trying to flip the aggregate verdict (e.g. to get a
            fraudulent training update accepted).
    """

    id: int
    strategy: str
    signal_noise: float = 0.1

    def __post_init__(self) -> None:
        if self.strategy not in STRATEGIES:
            raise ValueError(f"unknown strategy: {self.strategy!r}")
        if not 0.0 <= self.signal_noise < 0.5:
            raise ValueError("signal_noise must be in [0, 0.5)")

    def _observe(self, ground_truth: int, rng: random.Random) -> int:
        """Private noisy signal: correct w.p. 1 - signal_noise."""
        return ground_truth if rng.random() > self.signal_noise else 1 - ground_truth

    def report(self, ground_truth: int, rng: random.Random) -> int:
        if self.strategy == "lazy":
            return 1
        if self.strategy == "colluding":
            return 1
        signal = self._observe(ground_truth, rng)
        if self.strategy == "adversarial":
            return 1 - signal
        return signal  # honest
