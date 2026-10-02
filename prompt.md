# Repository prompt

The standing brief for work on this repository. Prompt version 1 (2026-10-02): the owner's rewrite of version 0
(kept in `meta/prompts/prompt-0.md`). Add `Prompt-Version: 1` to every commit.

## Mission
Build a public research portfolio (MIT-licensed) that supports PhD applications in ML/AI, robotics & autonomy, operations research, or industrial engineering in a CS / math / econ / finance department. Produce work a faculty member would take seriously: white papers written to publishable standard, reproducible code, implementations, and benchmarks. Quality beats volume.

## Direction
Computer science and AI applied to robotics and to other domains **where success can be measured and validated by a program**. Three tracks:

1. **Simulation and robotics.** Learning, estimation, planning and control where a simulator or dataset supplies ground truth: sim-to-real gaps, digital twins, perception and SLAM, manipulation, UAVs. Use an established simulator (MuJoCo, PyBullet, Gymnasium) or a public benchmark or log (e.g. EuRoC, KITTI, TUM RGB-D, D4RL, Open X-Embodiment) when the question is about real behaviour; a pure-Python model is fine when a closed form is the point, but then validate it against something independent.
2. **Empirical data analysis.** Public data from the empirical sciences and engineering (weather and climate, seismology, energy, materials, transport, biology, robot logs). Pose the question and the test before looking at the held-out part, and validate findings out of sample: a later period, another site, or a second dataset. Report effect sizes with uncertainty. A clean negative result is a result.
3. **Self-analysis of this repository's development.** The git history, `meta/runs.jsonl` and `meta/audits.jsonl` are a dataset about AI-agent research work: success and error rates, what predicts failures, and whether changes to this brief help. Treat changes to the brief as experiments (see Self-analysis).

The existing mechanism-design projects (scoring rules, markets, verification games, decentralised training) stay, but do not start new ones unless they have a simulator- or data-validated component. Improve old projects only where it raises their validation or fixes an error.

## Research groups to build on
Read their recent papers, code and project pages. Implement, reproduce, extend, and follow up the implications of their work.

Robotics & autonomy (priority):
- ARPG, Christoffer Heckman (CS): https://arpg.colorado.edu/
  Perception, SLAM, radar/lidar, field and subterranean robotics, vision-language navigation, generative 3D occupancy and scene synthesis.
  Directions: generative digital twins of environments, sensor simulation (especially radar), sim-to-real for perception, multi-robot mapping in simulation.
- CAIRO Lab, Bradley Hayes (CS): https://cairo-lab.com/
  Task and motion planning, learning from demonstration, explainable AI, human-robot collaboration.
  Directions: learning from demonstration inside digital twins, explainable planners evaluated in simulation, simulated human models for training collaborative robots.
- HIRO Group, Alessandro Roncone (CS): https://hiro-group.ronc.one/
  Embodied intelligence, social intelligence, robots in chemistry labs.
  Directions: digital twins of lab and manipulation workcells, embodied learning in simulation, sim-to-real for manipulation.
- Autonomous Systems IRT: https://www.colorado.edu/irt/autonomous-systems/
- RECUV (unmanned vehicles): https://www.colorado.edu/recuv/
  Directions: UAV and field-robot simulation, targeted observation of severe weather, safe autonomy with verification.

## Validation contract
Every new project, and every project a run changes substantively, meets all of these. `tools/check.py` enforces the mechanical parts on changed projects in CI.

- **A success criterion stated before the experiment.** The README opens with the question and a criterion with a threshold that a program decides, e.g. "the closed form agrees with a 10⁵-run Monte Carlo within 2 standard errors at every grid point", "the policy tuned in the twin keeps ≥ 90% of its return in the higher-fidelity simulator", "the effect has the same sign and p < 0.01 on 2020–2024 data held out from fitting". `experiments/run.py` prints `PASS` or `FAIL` for each criterion, and a unit test asserts it.
- **Independent validation.** The check compares against something the code under test did not produce: a closed form against simulation, a second implementation, an established simulator, a published number, or held-out data. Tests that only show the code agrees with itself are smoke tests; keep them, but they do not validate anything.
- **Every reported number comes from code.** Every number in the README and paper is printed by `experiments/run.py` into `experiments/results.txt`, and the run is seeded and deterministic. `tools/check.py --changed` re-runs it and fails on any difference or on a number it cannot trace.
- **Data is pinned.** Download it by script from a stable URL with a recorded sha256; commit small samples or derived summaries only. CI must be able to run the analysis on what is committed.
- **Dependencies.** Prefer the standard library. A project that needs packages pins them in `research/<slug>/requirements.txt`; CI installs every such file.
- **Prior art first.** Before writing, search for the closest existing results and cite them at the point of use. If the result is textbook, say so and present the work as a reproduction, a check, or a teaching example. Attribute a direction to a lab only when the lab's own pages or papers show it, and cite the specific paper.
- **No duplicates.** Search `research/` and the open PRs for a project on the same question first; extend it instead of starting a near-copy. Parallel sessions have built the same slug twice, so pick a slug no open PR uses and re-check before merging. If two projects overlap, each links the other and says what it adds.
- **Layout.** `README.md`, `paper/whitepaper.md` (motivation, related work, method, results, limitations, next steps, references), `src/<package>/`, `tests/`, `experiments/run.py`, `experiments/results.txt`, `pyproject.toml`. White papers and the site carry the AI-assistance disclosure.

## Quality budget
At least a third of every run goes to quality and reliability, done before new work and in the same PR:

1. **Red first.** If CI on `main` is red, or `python tools/check.py` reports an error, fix that before anything else.
2. **Audit one project at random.** `python tools/check.py --no-tests --repro-sample 1` picks and re-runs one. Then check its README and paper numbers against `results.txt`, verify every reference on the web, check its claims against its results and against prior art, and fix what you find. Append one line per check to `meta/audits.jsonl` (schema below), including a clean result.
3. **Pay down one debt item** from `python meta/process.py` (open debt) or `meta/QUEUE.md`: an untraced number, an uncited reference, a duplicate pair to merge, a missing validation criterion, a stale PR.

Then new work: **at most one new project per run**, and only one that meets the validation contract. Deepening an existing project (real data, a real simulator, an independent check) counts as new work and is usually worth more.

## Review gate
Before merging any PR:

1. `python tools/check.py --changed origin/main` passes locally, and `python site/build.py` prints `ok`.
2. A fresh subagent reviews the diff adversarially against this brief: numbers trace, claims follow from results, prior art is credited, citations are real and accurate, novelty is not overstated, and nothing duplicates an existing project. Fix every finding, or record why not in the run log. Count the findings.
3. CI is green on the PR's latest commit. Do not merge a PR in the minute it was opened; the review step comes first.

Merge other ready PRs only after they pass the same gate. Close PRs whose work already reached `main`, with a one-line comment.

## Run log
Every run appends exactly one line to `meta/runs.jsonl`; CI fails a PR that changes `research/` without one. Never edit past lines; append a correction line that references the original instead.
```json
{"date": "YYYY-MM-DD", "session": "<session url>", "prompt_version": 1,
 "input": "<the user or trigger message that started the run, verbatim>", "follow_up_inputs": ["<later user messages>"],
 "model": "<model id that made the commits>", "models_seen": ["<every model that served a turn>"],
 "started": "<ISO time>", "ended": "<ISO time>", "wall_minutes": 0,
 "tokens_in": null, "tokens_out": null, "cost_usd": null, "tool_calls": null,
 "task": "new-project|extend|fix|audit|merge|meta", "projects": ["<slug>"], "pr": "<url or null>",
 "commits": ["<sha>"], "lines_added": 0, "lines_removed": 0, "quality_share": 0.33,
 "merged": true, "ci_failures_before_green": 0, "review_findings": 0, "review_findings_fixed": 0,
 "audit_problems_found": 0, "tests_added": 0, "build_ok": true,
 "outcome": "success|partial|failed",
 "errors": ["short description of anything that went wrong"], "integrity_issues": [], "notes": ""}
```
Record every field you can observe and use `null` for the rest; take the model from the session metadata, not from memory. Redact secrets and personal data. A failed or abandoned run is data: log it.

`meta/audits.jsonl` takes one line per check of one project:
```json
{"date": "YYYY-MM-DD", "session": "<session url>", "auditor": "agent|human|ci", "kind": "repro|numbers|citations|claims|review",
 "slug": "<project>", "checked": 0, "problems": 0, "score": null,
 "findings": [{"kind": "citation-error|unverifiable-reference|uncited-reference|missing-prior-art|overclaim|text-error|unsupported-claim|unreproduced-number|duplicate|layout", "summary": "...", "fixed": true}]}
```

## Self-analysis
- End every run with `python meta/process.py --write`, which regenerates `meta/REPORT.md` (throughput, merge flow, rework, run outcomes by prompt version and model, audit error rates, open debt). Commit it with the run.
- Review session, about every 20 live runs: compare prompt versions and models on success rate, CI failures and review findings per run, audit problem rates, and tokens and time per merged project, with counts and intervals. Do not draw conclusions from fewer than about 10 runs per arm. Group runs by their starting input too.
- Candidate briefs live in `meta/prompts/prompt-<n>.md`, one focused change each, with the hypothesis and the metric it should move in `meta/prompts/experiments.md`. `meta/prompts/routing.json` (e.g. `{"champion": 1, "candidate": 2, "candidate_share": 0.2}`) routes runs: draw a uniform number at the start of a run and follow the candidate if it falls below the share. Promote a candidate only if it has no more integrity issues than the champion and is clearly better; retire it if it is worse.
- Copy the integrity, licensing and attribution sections unchanged into every candidate.

## Licensing & attribution
- Original work is MIT-licensed.
- Third-party code keeps its original license. Check compatibility before vendoring, and prefer dependencies over copying.
- Never imply affiliation with, or endorsement by, any lab, professor or company. Say "builds on" or "reproduces", never "with" or "for".

## Portfolio site
Maintain a GitHub Pages site listing each artifact: a one-line summary, related lab, and links to the paper, code and results. Keep it current as work merges (see `CLAUDE.md`).

## Research integrity
The goal is useful, publishable work that faculty are glad to see, never work that embarrasses them or the author. These rules hold in every prompt version and no experiment may relax them.
- Credit every idea, method, dataset, figure and piece of code that is not original, with a citation or link at the point of use. When a project reproduces a paper, say so in its title or first line.
- Never copy text from papers, theses or project pages without quoting and citing it. Paraphrase in your own words and still cite.
- Check every citation before merging: the paper exists, the authors, venue and year are right, and it says what you claim. Never invent a reference.
- Represent other groups' work accurately. If a reproduction disagrees with a published result, report it neutrally as a discrepancy with the setup and possible causes, never as an error by the authors.
- Do not overstate novelty or results. Say "stylised", "toy", "preliminary" or "negative" where it applies, and keep simulated results clearly separated from any claim about real systems.
- State that the work was produced with AI assistance in each white paper and in the portfolio site.
- Never contact, tag, mention or open issues on repositories of the professors, labs or authors cited. Outreach is the repository owner's decision.
