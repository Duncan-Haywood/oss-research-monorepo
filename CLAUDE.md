# Repo instructions

**Frozen, and the move has not landed.** The research portfolio is moving to
`Duncan-Haywood/fp-monorepo` under `research/`, in <https://github.com/Duncan-Haywood/fp-monorepo/pull/6143>. That pull
request is still open, so fp-monorepo's `main` has no `research/` until it merges. Do not add,
change or remove projects in this repository; it will be archived.

While the freeze holds, a scheduled run (one that starts with "read ./prompt.md") leaves no
trace. It creates no branch, commit, pull request or run-log line, and merges nothing. It replies
in one line and stops. Most of the unmerged branches here are no-op runs that logged themselves
on fresh branches.

## Land what you push

A branch that never reaches `main` is lost work: nobody sees it, and the next run redoes it.
When you push a branch here, open a pull request for it in the same run. Merge it yourself once
CI is green, or close it with a one-line reason. Never leave a branch without a pull request,
and never push to a branch whose pull request has merged. Scheduled runs follow the full rules
in `prompt.md` under Landing work.

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
