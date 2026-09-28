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
- `reputation.py` — a follow-up mechanism (see "Follow-up" section below)
  that bootstraps a per-verifier trust weight from PTS payoffs measured on a
  held-out calibration window, then uses it to repair Correlated
  Agreement's collusion vulnerability and to reputation-weight LMSR trades.

Run it:

```bash
cd research/decentralized-verification-markets
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 61 tests
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

## Follow-up: reputation-weighted mechanisms (closes Limitations 1-3, below)

The initial version of this package documented three limitations of its own
mechanisms as "natural next steps": Correlated Agreement's population-pooled
delta matrix is not collusion-resistant against a simultaneously-deviating
block; both mechanisms estimated their prior/delta matrix from the same
batch of reports they then scored (circular); and the LMSR aggregator
weighted every trade equally regardless of the trader's track record.
`reputation.py` addresses all three with one mechanism: it splits the task
stream into an early **calibration window** and a later **scoring window**,
computes each verifier's average Peer Truth Serum payoff on the calibration
window alone (PTS, not CA, because the base experiment above already found
PTS -- not CA -- robust to simultaneous correlated deviation), and squashes
that into a trust weight in `[floor, 1]` via a logistic. That weight is then
used, on the scoring window only, to:

1. **Re-estimate the CA delta matrix from trust-weighted pairs.** Each
   pair's contribution to the same-task / different-task counts is scaled by
   `min(weight_a, weight_b)`, so a low-trust pair barely influences the
   estimate (`trust_weighted_correlated_agreement_matrix`).
2. **Discount each CA payment by the payee's own trust weight**
   (`reputation_weighted_payment`). This turned out to be necessary *in
   addition to*, not instead of, step 1: downweighting low-trust pairs out
   of the delta-matrix estimate concentrates it on genuine honest-honest
   correlation and so *increases* its magnitude (verified empirically), which
   on its own makes a colluding block's free ride on `delta[(1, 1)]` more,
   not less, lucrative. Discounting the final payment by the payee's own
   weight closes that gap.
3. **Scale LMSR trade size by trust weight**
   (`reputation_weighted_trade_size`), so a low-trust reporter's trade moves
   the market price less.

**Result** (same 22-verifier population as above -- 14 honest / 3 lazy / 3
colluding / 2 adversarial -- `calibration_fraction=0.3`, `trust_steepness=12`,
scored on the held-out remainder; reproduce with
`experiments/run_experiment.py`):

| mechanism | honest advantage over best deviation |
|---|---|
| Correlated Agreement, plain (held-out scoring window) | **-1.73** (still broken) |
| Correlated Agreement, trust-weighted | **+14.12** (fixed) |

| market | Brier score (scoring window) |
|---|---|
| LMSR, plain | 0.0207 |
| LMSR, trust-weighted | **0.0107** (48% lower) |

Average calibration-window trust weight by strategy also separates cleanly
without being told which strategy is which ahead of time: honest ~0.95,
lazy/colluding ~0.46-0.48, adversarial at the floor (0.02).

**This fix has its own limitation, worth being explicit about in turn**: it
needs *enough* calibration-window data per agent for the bootstrapped PTS
score to separate strategies reliably -- at small `n_tasks` /
`calibration_fraction` (see `tests/test_simulation.py::TestTrustWeightedRepair`
for the scale that was empirically validated), honest agents' own per-task
noise can make an unlucky honest agent's calibration score overlap with the
lazy/colluding cluster's near-zero score, muting the fix. It also bootstraps
CA's fix off of PTS, so it inherits a dependency this package's original
result already flagged as one-directional: if PTS itself were compromised
(e.g. by an adversary that has learned to game PTS specifically, which
Limitation 4 below notes is unverified), the trust weights it produces would
be unreliable too.

## Follow-up 2: a trust-farming adversary, and rolling trust (Limitation 4)

Limitation 4 asked whether the trust bootstrap survives a mechanism-aware
adversary. It does not, against the most obvious one. `agents.py` now has a
**sleeper** strategy: honest until `switch_task` (default: the end of the
calibration window), then always reports "correct". Because
`reputation.py` freezes trust after one calibration window, sleepers earn
trust weight ~0.99 (indistinguishable from honest agents) and the
trust-weighted market gains nothing over the plain one.

`adaptive.py` adds **rolling (prequential) trust**: the scoring stream is
cut into blocks; block *k*'s weights come only from PTS payoffs on earlier
blocks (still out-of-sample), exponentially decayed by `decay`. Result
(14 honest + 7 sleepers, 1500 tasks, mean of 5 seeds; run
`experiments/run_experiment.py`):

| block size | decay | frozen-trust Brier | rolling-trust Brier | mean detection lag |
|---|---|---|---|---|
| 100 | 0.5 | 0.0169 | 0.0114 | 700 tasks (3/5 seeds) |
| 50 | 0.5 | 0.0169 | 0.0108 | 320 (5/5) |
| 25 | 0.5 | 0.0169 | 0.0110 | 170 (5/5) |
| 25 | 0.2 | 0.0169 | 0.0129 | 90 (5/5) |

Faster forgetting detects defection sooner but is noisier for honest
agents (Brier worsens at decay 0.2) -- the online-learning noise/latency
trade-off. Caveats: trust is a lagging signal, so every sleeper still gets
a window of undetected defection; a defector settles at weight ~0.5 (PTS ~
0 for uninformative reporters), not the floor; and only this one adaptive
strategy is tested. Adversaries that best-respond to PTS's prior estimate,
or that defect intermittently to stay above the trust threshold, remain
untested.

## Follow-up 3: an intermittent adversary, and asymmetric rolling trust

Follow-up 2 left "defect intermittently to stay above the trust threshold"
untested. `agents.py` now has an **intermittent** strategy: honest through
the calibration window, then in every `period`-task cycle honest for the
first `1 - defect_fraction` and always-"correct" for the rest. Against
symmetric rolling trust (Follow-up 2), honest phases buy trust back, so the
defense barely helps (12 honest + 10 intermittent, period 100, block 50,
mean of 5 seeds, scoring-window Brier):

| defect frac | plain | frozen | symmetric rolling (decay 0.5) | asymmetric rolling |
|---|---|---|---|---|
| 0.25 | 0.0119 | 0.0120 | 0.0119 | 0.0119 |
| 0.50 | 0.0214 | 0.0214 | 0.0210 | **0.0176** |
| 0.75 | 0.0309 | 0.0309 | 0.0265 | **0.0217** |

`rolling_trust_market(..., decay=0.2, recovery_decay=0.9)` is a
"fast down, slow up" update: a block scoring below the running average is
absorbed with `decay`, one scoring above it with the slower
`recovery_decay`. This is the usual asymmetry in adversarial online
learning (punish quickly, forgive slowly). It cuts the Brier excess by
~18% at 0.5 and ~30% at 0.75 defection. Costs and caveats: on an
all-honest population it raises Brier from 0.0017 to 0.0019 (honest noise
now gets punished faster than it is forgiven); at 0.25 defection it does
nothing measurable (little damage to prevent, and per-block PTS is too noisy
to catch it); and defectors are still only pushed toward the PTS ~ 0
logistic midpoint, never the floor. Adversaries that best-respond to PTS's
empirical prior remain untested.

## Follow-up 4: a stealth (PTS-aware) adversary, and minority-label trust

Follow-up 3 left "adversaries that best-respond to PTS" untested. The
`whitewash` strategy (`agents.py`) lies *only* when its signal says
"faulty": it reports "correct" with probability `whitewash_prob`, else is
honest. Faulty steps are the minority label, so the lie touches few tasks.
Two findings (14 honest + 8 whitewash, 1500 tasks, mean of 5 seeds):

1. **PTS itself stays incentive-compatible** (a whitewasher earns less than
   an honest verifier, ~0.22 vs ~0.44 per task at lie prob 0.5), but the
   *averaged* PTS score used for trust barely notices: average trust weight
   is still ~0.92 at lie prob 0.5. Trust-weighting therefore does nothing
   (Brier 0.0046 plain vs 0.0046 trust-weighted).
2. **Minority-label trust** (`stealth.py`) scores PTS only against peers who
   reported "faulty", where the `1/p(0)` factor makes a mismatch expensive,
   and centres trust at half the median verifier's score (no ground truth
   needed). Whitewasher weight drops to ~0.12 (honest ~1.0).

A subtlety worth recording: down-weighting trades alone *made things
worse* (Brier 0.0107) -- it fixed faulty steps but left LMSR liquidity `b`
fixed while total trade mass shrank, so clean steps became under-confident.
Scaling `b` by mean trust weight (b is an inverse learning rate in the
no-regret view) fixes it:

| lie prob | plain | avg-PTS trust | minority trust | minority, fixed b |
|---|---|---|---|---|
| 0.25 | 0.0022 | 0.0023 | 0.0021 | 0.0029 |
| 0.50 | 0.0046 | 0.0046 | **0.0023** | 0.0107 |
| 1.00 | 0.0205 | 0.0097 | **0.0025** | 0.0133 |

All-honest populations are unaffected (0.0017 either way). Caveats:
calibration-window only, so a whitewasher who is honest until the window
ends (sleeper + whitewash) is untested; it assumes an honest majority for
the median baseline; and lie prob 0.25 is too rare to detect from ~450
calibration tasks. Extending minority trust to the rolling scheme is the
natural next step.

## Follow-up 5: sleeper + whitewash, and rolling minority-label trust

Follow-up 4 named two open items: a whitewasher that is honest until the
calibration window ends, and extending minority trust to the rolling scheme.
The `late_whitewash` strategy (`agents.py`) is exactly that combination
(honest before `switch_task`, then `whitewash`). As predicted, calibration-
only minority trust is completely blind to it (Brier identical to plain).
`stealth.rolling_minority_trust_market` re-scores minority-label PTS on each
block, exponentially decayed, with liquidity scaled to trust mass. Result
(14 honest + 8 late_whitewash, 1500 tasks, block 100, decay 0.5, mean of 5
seeds, scoring-window Brier):

| lie prob | plain | frozen minority | rolling | rolling, asymmetric (recovery 0.9) |
|---|---|---|---|---|
| 0.5 | 0.0046 | 0.0046 | **0.0026** | 0.0028 |
| 1.0 | 0.0200 | 0.0200 | **0.0043** | 0.0043 |

That is a 43% and 79% reduction. Caveats: (a) each block holds few faulty
steps, so per-block minority scores are noisy and small blocks are
unreliable (the asymmetric variant gave no gain here since a whitewasher has
no honest phase to exploit); (b) detection still lags by roughly a block;
(c) the median baseline still assumes an honest majority; (d) a *intermittent*
whitewasher and a whitewasher that adapts its lie rate to the trust weight
remain untested; (e) all-honest populations are unaffected in the test
suite (|delta Brier| < 5e-4).

## Limitations (read before reusing this)

This is a research prototype, not a production-ready mechanism, and it
deliberately simplifies the underlying theorems in ways worth being
explicit about:

1. ~~**Correlated Agreement here is not collusion-resistant** against a
   *simultaneously* deviating block (the Dasgupta & Ghosh (2013)
   incentive-compatibility theorem is proved only for a single unilateral
   deviator).~~ **Closed** by the trust-weighted CA in the "Follow-up"
   section above — with the caveat, documented there, that the fix itself
   needs enough calibration-window data per agent to separate strategies
   reliably. The plain, population-pooled estimator (`peer_prediction.py`)
   is kept as-is and still exhibits the original vulnerability
   (`test_ca_is_vulnerable_to_simultaneous_correlated_deviation`); it is the
   thing being fixed, not something this package still claims is safe to
   use un-weighted.
2. ~~Both mechanisms used an *empirically estimated* prior/delta matrix
   computed from the same batch of reports being scored (circular).~~
   **Closed**: the trust-weighted path in `reputation.py` estimates trust
   and the CA delta matrix from a held-out calibration window, and scores
   both CA and LMSR only on the disjoint scoring window. The plain PTS/CA
   payoffs computed over the full stream (`result.pts_payoff`,
   `result.ca_payoff`) are still in-sample by design, since they are meant
   to reproduce the original (pre-follow-up) experiment for comparison.
3. ~~The LMSR aggregation treated every verifier's report as a fixed-size
   trade, not weighted by track record.~~ **Closed** by
   `reputation_weighted_trade_size` in the "Follow-up" section above.
4. The "adversarial" and "colluding" strategies here are simple,
   non-adaptive models. They do not attempt to game the specific mechanism
   (e.g. an adversary that has learned the empirical prior and best-responds
   against PTS specifically, or one that deliberately keeps its calibration-
   window PTS score just above the trust floor to blunt the Follow-up
   section's fix). Robustness against such an adaptive, mechanism-aware
   adversary is still unverified, and is the most natural next step from
   here. **Partially addressed** by Follow-up 2 (sleeper and intermittent
   trust-farming; stealth minority-label whitewashing addressed in Follow-up 4; sleeper+whitewash closed by Follow-up 5; intermittent whitewash and lie-rate-adaptive whitewash remain open).

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
