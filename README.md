# oss-monorepo
Duncan's open source software monorepo (MIT licensed). Portfolio page: `docs/index.html` (GitHub Pages, serve from `/docs`).

- [`research/decentralized-verification-markets`](research/decentralized-verification-markets) — peer-prediction and prediction-market mechanisms for verifying decentralized ML training, with adversarial evaluation.
- [`research/market-routing`](research/market-routing) — cost-function markets as expert routers: LMSR = Hedge, quadratic potential = sparsemax; regret/loss bounds verified, continual-learning simulation.
- [`research/wagering-modular-experts`](research/wagering-modular-experts) — self-financed wagering mechanisms as verifiable routers for modular, continually learning experts; shows plain WSWM locks in under recurring regimes and a fixed-share tax fixes it at the cost of subsidising free-riders.
- [`research/property-elicitation-verification`](research/property-elicitation-verification) — property elicitation (quantile/expectile/Bregman scores, non-elicitability of variance) applied to pricing tail-drift tolerance thresholds in verifiable ML training.
- [`research/verification-game`](research/verification-game) — inspection-game economics of refereed verification: stake substitutes for re-execution, extra verifiers free-ride, and optimal tolerance/stake under floating-point drift.
- [`research/verifier-bribery`](research/verifier-bribery) — bribing verifiers in refereed verification: closed-form bribe floor, a sharp collusion-proof stake that falls as 1/m, and jackpots that raise the floor one-for-one.
- [`research/reproducible-refereed-training`](research/reproducible-refereed-training) — measured float32 reduction-order drift, RepOps-style canonical order, Merkle-committed training traces with a teacher-forced referee; per-step tolerance is a cumulative hidden-deviation budget.
- [`research/private-markets`](research/private-markets) — differentially private LMSR via the binary-tree mechanism: path-wise loss bound, and the accuracy/subsidy cost of privacy.
- [`research/audit-dynamics`](research/audit-dynamics) — no-regret learning in the refereed-verification inspection game: conserved potential, closed-form cycle period, averages converge but per-round audit probability collapses; optimistic Hedge converges.
