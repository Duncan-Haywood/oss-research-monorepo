# Agent runs traced from commit trailers

- Sessions named in commits: **266**
- Transcript still retrievable: **179**
- Total recorded cost of retrievable runs: **$133.23** (mean $0.74)

| Month (first commit) | not found | found |
|---|---|---|
| 2026-09 | 70 | 174 |
| 2026-10 | 17 | 5 |

| Retrievable runs by session title | count |
|---|---|
| ⚡ oss 4 | 46 |
| ⚡ oss 2 | 45 |
| ⚡ oss 3 | 45 |
| ⚡ oss 1 | 42 |
| GitHub Pages homepage setup | 1 |

| Prompt version | runs |
|---|---|
| A | 114 |
| A2 | 5 |
| B | 4 |
| C | 46 |
| C2 | 9 |
| custom | 1 |

## What could not be retrieved, and why (as of 2026-10-01)

- Only runs of the four "oss" routines on the account that owns them (from 2026-09-29 01:08Z)
  and one desktop session are readable. Prompt and result text for those runs is kept in the
  private `fp-monorepo` under `.claude/harvest/`, not here, because this repository is public.
- **8 sessions from 2026-09-28** (the trust / peer-prediction follow-ups) predate every visible run.
- **79 sessions from 2026-09-30 08:10Z to 2026-10-01 04:36Z**, mostly "Add X-twin" projects,
  come from a second set of about four hourly runs that this account cannot see: different
  branch-name families, committing earlier in each hour. Another account, workspace or deleted
  records would all explain it.
- The four visible routines received five successive prompt versions (A, A2, B, C, C2); the
  current one is `.claude/routines/research-loop.md`.

Regenerate: `python3 session_harvest.py extract`, run the agent harvest described in the
docstring, then `python3 session_harvest.py report <harvest.jsonl> --csv runs.csv --md runs.md --public`.
