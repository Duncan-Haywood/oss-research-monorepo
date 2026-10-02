# Quality queue

Open debt and follow-ups, highest value first. Each run's quality budget (see `prompt.md`) takes at least one item.
Remove an item in the PR that finishes it; add new items as you find them.

## Validation upgrades (the pivot)
- [ ] Ground one twin project on real data. The closest fits are the odometry and loop-closure twins (`odometry-twin`,
  `loop-closure-twin`, `loopclosure-twin`): measure the drift-misspecification ratio ρ from EuRoC MAV or KITTI odometry
  residuals instead of assuming it, and state a pass/fail criterion first.
- [ ] Run `twin-transfer` on a real simulator plant (e.g. a MuJoCo pendulum or cart-pole) instead of the scalar model,
  with the twin as a lower-fidelity MuJoCo model.
- [ ] Check `radar-detection-twin` / `cfar-family-twin` against a public automotive radar dataset (e.g. RadarScenes),
  or narrow their claims to the stylised model.
- [ ] Start the self-analysis track as a research project: pre-register hypotheses about agent-built research
  (e.g. "the version-1 quality budget lowers the audit problem rate per project") and test them on
  `meta/runs.jsonl` and `meta/audits.jsonl` once about 10 live runs exist.
- [ ] Add a stated pass/fail success criterion (printed `PASS`/`FAIL` by `run.py`, asserted by a test) to existing
  projects, starting with the featured ones in `site/projects.json`.

## Stale pull requests
Nine of the 11 open PRs are rival versions of a project that a parallel session also built and merged under the same
slug; their content differs from `main`. For each, compare with `main`, carry over anything better through a normal
PR, then close it with a one-line comment.
- [ ] #242 `rain-twin`, #237 `sweep-twin` (its `multi-observation-elicitation` is identical to main), #205 `flex-twin`,
  #198 `backlash-twin`, #191 `sync-twin`, #151 `loop-closure-twin`, #146 `grasp-twin`, #118 `delayed-outer`,
  #67 `ordinal-scores`.
- [ ] #34 `tail-elicitation` is not on `main`; check whether `tail-risk-elicitation` supersedes it.
- [ ] #227 is identical to `main` for every project it touches: close it.

## Duplicates
Each pair now links the other in a "Related projects" section (2026-10-02). Recommendations from that review; merge
by folding the later project's genuinely new results into the survivor and removing the other slug from `research/`,
`README.md` and `site/projects.json` in one PR:
- [ ] `loopclosure-twin` into `loop-closure-twin` (static gate model vs the dynamic filter; one question). Mention
  `odometry-twin`, a third pass at the same gate-recall question.
- [ ] `delayed-outer` into `outer-delay` (same Levin–May stability law).
- [ ] `compressed-outer` into `compressed-sync` (identical floor and stability formula).
- [ ] `interval-scores` into `interval-elicitation` (re-derives the Winkler-score results).
- [ ] `cfar-family-twin` into `radar-detection-twin` (re-derives the 30×/35× inflation and "CA best after repair").
- `alias-twin` and `aliasing-twin`: keep both (different estimators and repairs); they now cross-link.

## Debt reported by `tools/check.py` (warnings)
- [ ] Numbers in write-ups that no experiment prints (`[numbers]` warnings, about 80 projects). Make `run.py` print
  the value, or correct the text.
- [ ] Reference-list entries never cited in the text (`[citations]` warnings, about 300 entries). Several twin papers
  append the same off-topic sim-to-real survey. Cite at the point of use or remove.
- [ ] `decentralized-verification-markets`, `property-elicitation-verification`, `wagering-modular-experts` have no
  `paper/whitepaper.md` (their READMEs are the write-up); listed in `LEGACY` in `tools/check.py`.

## Attribution
- [ ] Lab tags: several READMEs attribute research directions to a lab that come from this repository's own brief rather
  than the lab's pages or papers. Re-check each tag against the lab's own site and cite a specific paper, or drop it.

## Owner actions (cannot be done from a session)
- [ ] Make the `Checks` workflow a required status check on `main` (Settings → Branches), so nothing merges red.
- [ ] Decide on <https://github.com/Duncan-Haywood/fp-monorepo/pull/6143>: if the move goes ahead, bring this
  repository's commits since 2026-10-01 across before archiving it.
