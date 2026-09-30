# Repo instructions

## Keep the GitHub Pages homepage up to date

The portfolio homepage <https://duncan-haywood.github.io/oss-research-monorepo/> is
`docs/index.html`, deployed by `.github/workflows/pages.yml` on every push to `main`.
It must list every project in `research/`, in the same order as the README.

Whenever you add, rename or remove a project under `research/`, or change its headline
results, in the same commit:

1. Update its bullet in `README.md` (`- [`research/<name>`](research/<name>) — one-line summary.`).
2. Update `docs/index.html`: append (or edit) an entry before `</body></html>`:
   ```html
   <h2>Question the project answers?</h2>
   <p>Plain-language summary with the key quantitative results, the model's main
   limitations, and "Pure-Python, N tests."</p>
   <p><a href="https://github.com/Duncan-Haywood/oss-research-monorepo/tree/main/research/<name>">Code and white paper</a></p>
   ```
   Use HTML entities for maths symbols (`&minus;`, `&radic;`, `&times;`, `<sub>`, `<sup>`)
   as existing entries do; keep the page a single self-contained file (no external assets).
3. Run `python scripts/check_pages.py` and make sure it prints `ok`. The same check runs
   in CI on every pull request and blocks the deploy if it fails.
