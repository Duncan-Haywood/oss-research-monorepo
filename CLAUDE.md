# Repo instructions

Read `prompt.md` first. It is the standing brief: direction, validation contract, quality budget, review gate and run log.

## Status
A move into `Duncan-Haywood/fp-monorepo` under `research/` is proposed in
<https://github.com/Duncan-Haywood/fp-monorepo/pull/6143>, which is open and not merged. Until the owner merges
it, this repository is where the work happens. If it merges, bring this repository's later commits across
before archiving this one.

## Checks
- `python tools/check.py` runs every project's unit tests plus the layout, AI-disclosure, number-tracing, citation
  and duplicate checks. Before every PR run `python tools/check.py --changed origin/main`: it is strict on the
  projects you changed, re-runs their `experiments/run.py` against `results.txt`, and requires a new line in
  `meta/runs.jsonl`. CI (`.github/workflows/checks.yml`) runs the same, plus a weekly reproducibility audit.
- `python meta/process.py --write` regenerates `meta/REPORT.md`. Log your run in `meta/runs.jsonl` and your audits
  in `meta/audits.jsonl` (schemas in `prompt.md`); open debt and follow-ups live in `meta/QUEUE.md`.
- Some projects import sibling packages. `tools/check.py` puts every `research/*/src` on `PYTHONPATH`; by hand, use
  the `PYTHONPATH` line in the project's README.

## Keep the GitHub Pages homepage up to date

The portfolio homepage <https://duncan-haywood.github.io/oss-research-monorepo/> is generated
by `site/build.py` and deployed by `.github/workflows/pages.yml` on every push to `main`.
Nothing under `site/` is published directly; the build writes `_site/index.html` (gitignored).

Sources:
- `site/projects.json` — themes (id, name, blurb), the `featured` slugs, and per project:
  `slug`, `title` (a question the project answers), `summary` (the abstract, HTML).
- `README.md` — each project's bullet is reused as the card's one-line lede.
- `research/<slug>/` — test counts are the `def test_` functions in its `test*.py` files.
- `site/template.html` — layout, styles and search script.

Whenever you add, rename or remove a project under `research/`, or change its headline
results, in the same commit:

1. Update its bullet in `README.md`: ``- [`research/<name>`](research/<name>) — one-line summary.``
2. Add or edit its entry in `site/projects.json`, in the theme it fits best:
   ```json
   {"slug": "<name>", "title": "Question the project answers?",
    "summary": "Plain-language abstract with the key quantitative results and the model's main limitations (e.g. Stylised.)."}
   ```
   The summary is HTML: use entities for maths (`&minus;`, `&radic;`, `&times;`, `<sub>`, `<sup>`, `<em>`).
   Don't write the test count; the build adds it. Add a new theme only if several projects
   need it, and give it a `--t-<id>` colour in both the light and dark blocks of `site/template.html`.
3. Run `python site/build.py` and make sure it prints `ok`. It fails if any `research/`
   project is missing from `projects.json` or `README.md`, or if either lists one that no
   longer exists. CI runs the same build on every pull request and it blocks the deploy.
   Open `_site/index.html` to preview.
