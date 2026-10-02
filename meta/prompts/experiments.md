# Prompt experiments

One entry per brief version: what changed, why, the metric it should move, and the result.

## Version 0 (2026-09-28 to 2026-10-01): original brief
Throughput-oriented: no quality budget, CI built only the homepage, no run log in practice. The runs are backfilled in
`meta/runs/backfill-v0.jsonl` from git history, so only merged work is visible. Baseline from the audit of
2026-10-02 (`meta/audits/`): 16 of 16 re-run experiments reproduced byte for byte, but no paper disclosed AI
assistance, 6 of 15 audited projects missed directly relevant prior art, and the checker could not trace at least one
number in the write-up of about 1 project in 3 (some of those are derived values, so this is an upper bound).

## Version 1 (2026-10-02): owner's rewrite, not a randomised experiment
Changes: the direction moves to programmatically validated work (simulation and robotics, empirical data, self-analysis
of development); a validation contract per project; a quality budget of at least a third of each run; a review gate
before merge; a mandatory run log enforced by CI; `tools/check.py` in CI on every PR.
Hypothesis: fewer integrity issues and audit problems per project, at the cost of fewer new projects per run.
Metrics: audit problem rate per project checked, review findings and CI failures per run, integrity issues, and new
projects per run. Compare version 1 live runs with version 0 audits; this is a before/after comparison, not a
randomised one, so read it with care.
Result: pending (needs about 10 live runs).
