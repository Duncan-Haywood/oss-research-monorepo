# `.claude/`: how agent work in this repo is tracked

| Path | What | Written by |
|---|---|---|
| `routines/<name>.md` | The instructions a scheduled routine follows. The routine itself only says "read this file from `main`", so every change to its behaviour is a reviewed, dated commit. | You, via PR |
| `prompts/<date>/<session>.md` | Every prompt sent to an agent session, verbatim, appended as it is sent (credential-shaped strings masked). | `hooks/log_prompt.py`, a `UserPromptSubmit` hook |
| `runs/<timestamp>-<session>.json` | One record per routine run: prompt commit SHA, outcome, PRs merged, summary. | The agent, at the end of each run |
| `harvest/` | `session_harvest.py` traces commit trailers back to sessions; `runs.md` / `runs.csv` hold what could still be retrieved. Public repo: metadata only. | Agent-driven harvest |

To answer "which instructions produced this project?": find the project's commits, read the
session ID in their trailers, then open `prompts/*/<session>.md` and `runs/*-<session>.json`.
