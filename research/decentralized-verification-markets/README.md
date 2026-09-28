# Peer-prediction markets for decentralized ML training verification

A small, dependency-free research implementation connecting two bodies of
work:

- **Algorithmic economics / information elicitation**: proper scoring
  rules, prediction markets, and peer prediction, as studied by the
  [CU Boulder Algorithmic Economics group](https://www.colorado.edu/cs-theory/alg-econ)
  (Rafael Frongillo and Bo Waggoner's lab), [Bo Waggoner](https://www.bowaggoner.com/)
  and [Rafael Frongillo](https://raf.prof/index.html).
- **Verifiable / decentralized ML training**, as studied by
  [Gensyn's research team](https://www.gensyn.ai/research) — notably
  Frongillo, who is concurrently Head of Research at Gensyn, and Gensyn
  researchers [Gabriel Andrade](https://www.gensyn.ai/team/gabriel-andrade),
  [Oğuzhan Ersoy](https://www.gensyn.ai/team/oguzhan-ersoy) and
  [Marx Zang](https://www.gensyn.ai/team/marx-zang).

## The idea

Gensyn's **Verde** verifies distributed training by having a referee
recompute a training step and compare it against the claimed result — this
is unconditionally correct but expensive: it requires paying for the
computation twice. Gensyn's **Credibly Neutral AI Oracles** (Monroe &
Andrade) instead uses a supermajority-dispute mechanism over an independent
"report layer" and proves a bound of `eps * (1 - eps)` on the probability of
reaching the wrong verdict, where `eps` is the fraction of misreporting
participants — but it still assumes report-layer independence and doesn't
use *peer* correlation between reporters to get information for free.

Separately, Gensyn's post
["Prediction Markets are Learning Algorithms"](https://www.gensyn.ai/research/prediction-markets-are-learning-algorithms)
observes that bounded-loss cost-function market makers (e.g. Hanson's LMSR)
are mathematically equivalent to no-regret online learning algorithms (Chen
& Vaughan, 2010; Frongillo, Della Penna & Reid, 2012: Kelly-bettor CFMs are
exactly stochastic mirror descent).

This project asks: **can peer prediction — a proper-scoring-rule mechanism
that elicits honest reports using only *other agents'* reports as the
scoring reference, with no ground truth required — replace most of the
ground-truth recomputation in a Verde-style verification pipeline, while
staying incentive-compatible against lazy, colluding, and adversarial
verifiers?** And can an LMSR market maker, exploiting the online-learning
equivalence, aggregate those reports into a single calibrated
"probability this step was computed correctly" as they arrive, without a
separate batch tallying step?

## What's implemented

`src/verification_markets/`:

- `scoring_rules.py` — strictly proper scoring rules (log, Brier,
  spherical), with a numerical properness check (Gneiting & Raftery, 2007).
- `peer_prediction.py` — two peer-prediction mechanisms specialized to
  binary reports:
  - **Peer Truth Serum (PTS)** (Jurca & Faltings, 2009; Faltings &
    Radanovic, 2017): pays an agent by comparing their report to a random
    peer's, scaled by the inverse of the peer's (empirically estimated)
    marginal report probability, so that any *uninformative* fixed/random
    reporting strategy earns ~0 expected payment while truthful reporting
    earns strictly more.
  - **Correlated Agreement (CA)** (Dasgupta & Ghosh, 2013), a simplified
    practical variant: estimates a "same task vs. different task" delta
    matrix over the population's pairwise reports and pays agreement that is
    more common on shared tasks than a cross-task shuffle baseline would
    predict.
- `market_maker.py` — an LMSR cost-function market maker (Hanson, 2003).
- `agents.py` — verifier strategies: `honest`, `lazy` (free-rides, always
  reports "correct"), `colluding` (a coordinated block that always reports
  "correct"), `adversarial` (reports the negation of its true signal).
- `simulation.py` / `metrics.py` — a simulation harness for a stream of
  synthetic training-step tasks (each faulty with some corruption rate),
  and metrics: incentive-compatibility gap, LMSR calibration (Brier score),
  majority-vote error rate, audit-cost savings, and an empirical
  manipulation-vulnerability curve compared against Credibly Neutral AI
  Oracles' `eps * (1 - eps)` bound.

Run it:

```bash
cd research/decentralized-verification-markets
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 32 tests
python3 experiments/run_experiment.py                       # full report
```

No third-party dependencies (pure standard library), so no install step is
required.

## Results (from `experiments/run_experiment.py`, seed 42, 2000 tasks, 15%
corruption rate, 14 honest / 3 lazy / 3 colluding / 2 adversarial verifiers)

**Incentive compatibility** (average payoff per verifier, by strategy):

| mechanism | honest | lazy | colluding | adversarial | honest advantage |
|---|---|---|---|---|---|
| Peer Truth Serum | **+519.88** | -30.20 | -30.62 | -734.32 | **+550.08** |
| Correlated Agreement | +23.63 | +27.51 | **+27.29** | -24.82 | **-3.87** |

PTS stays robustly incentive-compatible even under a heavy, simultaneous
mix of deviating strategies. CA does not — see **Limitations** below; this
is a real, reproducible finding, not a tuning artifact (see
`tests/test_simulation.py::test_ca_is_vulnerable_to_simultaneous_correlated_deviation`).

**Aggregate accuracy**: the LMSR market's price tracks ground truth with a
Brier score of **0.0203** (0 = perfect, 0.25 = an uninformative 50/50
market), and a simple majority vote over all 22 verifiers' reports is wrong
on only **1.75%** of tasks.

**Audit cost savings**: with a 5% audit fraction, **95%** of training steps
never need full ground-truth recomputation — peer prediction and the market
price stand in for it.

**Manipulation vulnerability** (majority-vote error vs. the Credibly
Neutral AI Oracles `eps * (1 - eps)` bound, swept over the fraction `eps`
of non-honest verifiers, 1200 tasks, 20% corruption rate):

| eps (non-honest fraction) | empirical majority-vote error | eps·(1-eps) bound |
|---|---|---|
| 0.05 | 0.0000 | 0.0475 |
| 0.20 | 0.0017 | 0.1600 |
| 0.40 | 0.0558 | 0.2400 |
| 0.60 | 0.2000 | 0.2400 |
| 0.80 | 0.2000 | 0.1600 |

The empirical majority-vote error stays *below* the theoretical bound
across the swept range, and (as expected) degrades sharply once non-honest
verifiers are the majority (`eps >= 0.5`) — majority vote has no reason to
track truth once honest reporters are outnumbered. Note the bound in
Credibly Neutral AI Oracles is proved for a different mechanism
(supermajority dispute over an independent report layer); the comparison
here is illustrative, not a claim that majority vote satisfies the same
guarantee.

## Limitations (read before reusing this)

This is a research prototype, not a production-ready mechanism, and it
deliberately simplifies the underlying theorems in ways worth being
explicit about:

1. **Correlated Agreement here is not collusion-resistant.** The Dasgupta &
   Ghosh (2013) incentive-compatibility theorem is proved for a *single*
   agent unilaterally deviating while the rest of the population reports
   honestly. This implementation estimates a single delta matrix pooled
   across the *entire* population, including any simultaneously-deviating
   sub-population's own reports. When a large enough lazy/colluding block
   all report the (skewed) majority label, the pooled matrix ends up
   dominated by genuine honest-honest correlation, and the deviating block
   free-rides on it — see the results table above and
   `test_ca_is_vulnerable_to_simultaneous_correlated_deviation`. Peer Truth
   Serum does not have this failure mode in the same experiment, because
   dividing by the peer's marginal report probability directly cancels out
   the "always guess the popular answer" exploit. A faithful fix would
   likely require per-agent-pair delta estimation with enough shared-task
   history per pair, or an explicit collusion-detection pass before scoring
   — both are natural next steps.
2. Both mechanisms use an *empirically estimated* prior/delta matrix
   computed from the same batch of reports being scored, rather than a
   held-out calibration window. In a live deployment you would want to
   estimate these from historical (already-audited) data to avoid any
   circularity.
3. The LMSR aggregation treats every verifier's report as a fixed-size
   trade; it does not yet weight trades by a verifier's track record (e.g.
   their historical peer-prediction score), which is the natural next
   extension — and would let the market itself down-weight known-bad
   actors over time.
4. The "adversarial" and "colluding" strategies here are simple,
   non-adaptive models. They do not attempt to game the specific mechanism
   (e.g. an adversary that has learned the empirical prior and best-responds
   against PTS specifically). Robustness against an adaptive, mechanism-aware
   adversary is unverified.

## Citations

- Gneiting, T. & Raftery, A. (2007). "Strictly Proper Scoring Rules,
  Prediction, and Estimation." *JASA*.
- Hanson, R. (2003). "Combinatorial Information Market Design."
- Jurca, R. & Faltings, B. (2009). "Mechanisms for Making Crowds Truthful."
  See also Faltings, B. & Radanovic, G. (2017), *Game Theory for Data
  Science: Eliciting Truthful Information* (Peer Truth Serum, ch. 4).
- Dasgupta, S. & Ghosh, A. (2013). "Crowdsourced Judgement Elicitation with
  Endogenous Proficiency." (Correlated Agreement.)
- Chen, Y. & Vaughan, J. W. (2010). "A New Understanding of Prediction
  Markets via No-Regret Learning."
- Frongillo, R., Della Penna, N. & Reid, M. (2012). "Interpreting Prediction
  Markets: A Stochastic Approach."
- Gensyn AI, "Prediction Markets are Learning Algorithms" —
  https://www.gensyn.ai/research/prediction-markets-are-learning-algorithms
- Gensyn AI, "Verde: A Verification System for Machine Learning over
  Untrusted Nodes" —
  https://www.gensyn.ai/research/verde-a-verification-system-for-machine-learning-over-untrusted-nodes
- Monroe, M. & Andrade, G., "Credibly Neutral AI Oracles" —
  https://www.gensyn.ai/research/credibly-neutral-ai-oracles
- Waggoner, B., "An Axiomatic Study of Scoring Rule Markets"; "Informational
  Substitutes"; "Bounded-Loss Private Prediction Markets" —
  https://www.bowaggoner.com/
