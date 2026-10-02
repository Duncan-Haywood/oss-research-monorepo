"""Self-analysis of how this repository is built: throughput, merge flow, rework, reproducibility and audit error rates.

    python meta/process.py              # print the report (markdown)
    python meta/process.py --write      # also write meta/REPORT.md
    python meta/process.py --backfill   # append a backfilled line to meta/runs.jsonl for each session in git history
                                        # that has none yet (needs full history: git fetch --unshallow)
    python meta/process.py --check      # validate meta/runs.jsonl and meta/audits.jsonl, then print the report

Sources: git history (Claude-Session and Co-Authored-By trailers, "Merge pull request #N" commits), meta/runs.jsonl
(one line per agent run; see prompt.md) and meta/audits.jsonl (one line per audit of one project). Nothing here
calls the network; PR outcomes that git cannot see (closed without merging, CI failures, review comments) must be
recorded by the run itself in meta/runs.jsonl.
"""
import argparse
import json
import math
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS, AUDITS, REPORT = ROOT / "meta" / "runs.jsonl", ROOT / "meta" / "audits.jsonl", ROOT / "meta" / "REPORT.md"
RUN_KEYS = ("date", "session", "prompt_version", "model", "task", "outcome", "projects")
AUDIT_KEYS = ("date", "session", "auditor", "kind", "slug", "checked", "problems")
BULK = 20  # a commit touching more projects than this is a repo-wide edit, not rework of a project


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def commits():
    """Non-merge commits, oldest first, with session, model, time, numstat and touched projects."""
    sep, out = "\x1e", []
    raw = git("log", "--reverse", "--no-merges", "--numstat",
              f"--format={sep}%H%x1f%aI%x1f%s%x1f%(trailers:key=Claude-Session,valueonly,separator=%x2C)"
              "%x1f%(trailers:key=Co-Authored-By,valueonly,separator=%x2C)%x1f%(trailers:key=Prompt-Version,valueonly)")
    for block in raw.split(sep)[1:]:
        head, _, stat = block.partition("\n")
        sha, date, subject, session, model, pv = (head.split("\x1f") + [""] * 6)[:6]
        added = removed = 0
        files = []
        for line in stat.strip().splitlines():
            a, r, f = (line.split("\t") + ["", ""])[:3]
            added += int(a) if a.isdigit() else 0
            removed += int(r) if r.isdigit() else 0
            files.append(f)
        model = re.sub(r"\s*<.*", "", model.split(",")[0]).strip() or None
        out.append({"sha": sha, "time": datetime.fromisoformat(date), "subject": subject, "session": session.strip() or None,
                    "model": model, "prompt_version": int(pv) if pv.strip().isdigit() else None, "added": added,
                    "removed": removed, "files": files,
                    "projects": sorted({f.split("/")[1] for f in files if f.startswith("research/") and f.count("/") >= 2}),
                    "new": sorted({f.split("/")[1] for f in files if re.fullmatch(r"research/[^/]+/README\.md", f)})})
    return out


def merges():
    """(PR number, merge time, branch first-commit time) for every merged PR."""
    out = []
    for line in git("log", "--merges", "--format=%H%x1f%aI%x1f%s").splitlines():
        sha, date, subject = line.split("\x1f")
        m = re.match(r"Merge pull request #(\d+) from \S+", subject)
        if not m:
            continue
        first = git("log", "--reverse", "--format=%aI", f"{sha}^1..{sha}^2").split()
        out.append((int(m.group(1)), datetime.fromisoformat(date), datetime.fromisoformat(first[0]) if first else None))
    return sorted(out)


def created_projects(cs):
    """slug -> first commit that added its README (only for projects that still exist)."""
    alive = {p.name for p in (ROOT / "research").iterdir() if p.is_dir()}
    first = {}
    for c in cs:
        for s in c["new"]:
            if s in alive and s not in first and (ROOT / "research" / s / "README.md").exists():
                first[s] = c
    return first


def load_jsonl(path):
    if not path.exists():
        return []
    rows = []
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if line.strip():
            rows.append((i, json.loads(line)))
    return rows


def validate():
    errs = []
    for path, keys in ((RUNS, RUN_KEYS), (AUDITS, AUDIT_KEYS)):
        try:
            rows = load_jsonl(path)
        except json.JSONDecodeError as e:
            errs.append(f"{path.relative_to(ROOT)}: bad JSON ({e})")
            continue
        for i, r in rows:
            missing = [k for k in keys if k not in r]
            if missing:
                errs.append(f"{path.relative_to(ROOT)}:{i}: missing {', '.join(missing)}")
    return errs


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def pct(k, n):
    if not n:
        return "n/a"
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.0f}% (95% CI {100 * lo:.0f}–{100 * hi:.0f}%)"


# ---- backfill ------------------------------------------------------------------------------------

def backfill(cs):
    have = {r.get("session") for _, r in load_jsonl(RUNS)}
    by_session = defaultdict(list)
    for c in cs:
        if c["session"]:
            by_session[c["session"]].append(c)
    lines = []
    for session, group in sorted(by_session.items(), key=lambda kv: kv[1][0]["time"]):
        if session in have:
            continue
        new = sorted({s for c in group for s in c["new"]})
        touched = sorted({s for c in group for s in c["projects"]})
        subjects = " ".join(c["subject"] for c in group).lower()
        task = ("new-project" if new else "fix" if re.search(r"\bfix|correct", subjects) else
                "extend" if touched else "meta")
        t0, t1 = group[0]["time"], group[-1]["time"]
        lines.append({
            "date": t0.date().isoformat(), "session": session, "prompt_version": 0, "backfilled": True,
            "input": None, "follow_up_inputs": None, "model": group[-1]["model"],
            "models_seen": sorted({c["model"] for c in group if c["model"]}),
            "started": t0.isoformat(), "ended": t1.isoformat(),
            "wall_minutes": round((t1 - t0).total_seconds() / 60, 1) if len(group) > 1 else None,
            "tokens_in": None, "tokens_out": None, "cost_usd": None, "tool_calls": None,
            "task": task, "projects": new or touched, "pr": None, "commits": [c["sha"][:7] for c in group],
            "lines_added": sum(c["added"] for c in group), "lines_removed": sum(c["removed"] for c in group),
            "merged": True, "ci_failures_before_green": None, "review_findings": None,
            "tests_added": None, "build_ok": None, "outcome": "success", "errors": [], "integrity_issues": [],
            "notes": "backfilled from git history: merged work only; abandoned runs and CI history are not visible"})
    with RUNS.open("a") as f:
        for l in lines:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
    return len(lines)


# ---- report --------------------------------------------------------------------------------------

def report():
    cs, ms = commits(), merges()
    runs = [r for _, r in load_jsonl(RUNS)]
    audits = [r for _, r in load_jsonl(AUDITS)]
    created = created_projects(cs)
    out = ["# Process report", "",
           f"Generated by `meta/process.py` from git history up to `{git('rev-parse', '--short', 'HEAD').strip()}`, "
           f"`meta/runs.jsonl` ({len(runs)} runs) and `meta/audits.jsonl` ({len(audits)} audit lines). "
           "Rates carry Wilson 95% intervals; small samples are wide on purpose.", ""]

    # Throughput
    per_day = Counter(c["time"].date().isoformat() for c in created.values())
    sessions = {c["session"] for c in cs if c["session"]}
    models = Counter(c["model"] for c in cs if c["model"])
    out += ["## Throughput", "",
            f"- {len(cs)} non-merge commits, {len(sessions)} agent sessions, {len(created)} live projects.",
            "- Projects added per day: " + ", ".join(f"{d} {n}" for d, n in sorted(per_day.items())) + ".",
            "- Commits by model: " + ", ".join(f"{m} {n}" for m, n in models.most_common()) + ".", ""]

    # Merge flow
    if ms:
        nums = [n for n, _, _ in ms]
        lat = sorted((t - f).total_seconds() / 60 for _, t, f in ms if f)
        top = max(nums)
        out += ["## Merge flow", "",
                f"- {len(ms)} PRs merged; the highest PR number seen is #{top}, so up to {top - len(ms)} numbers were "
                "PRs closed without merging, still open, or issues (git cannot tell which).",
                f"- First commit on the branch to merge: median {statistics.median(lat):.0f} min, "
                f"90th percentile {lat[int(0.9 * (len(lat) - 1))]:.0f} min. Minutes from commit to merge leave no room "
                "for review; this is a proxy for the review gate.", ""]

    # Rework
    rework, fixes = Counter(), 0
    for c in cs:
        if len(c["projects"]) > BULK:
            continue
        if re.match(r"(fix|correct|revert)", c["subject"], re.I):
            fixes += 1
        for s in c["projects"]:
            first = created.get(s)
            if first and c["sha"] != first["sha"] and c["session"] != first["session"] \
                    and c["time"] - first["time"] <= timedelta(days=14):
                rework[s] += 1
    out += ["## Rework", "",
            f"- Projects edited again by a later session within 14 days of creation (repo-wide edits of more than "
            f"{BULK} projects excluded): {pct(len(rework), len(created))}.",
            f"- Commits whose subject starts with Fix/Correct/Revert: {fixes} of {len(cs)}.",
            "- Low rework means few projects were revisited, not that few needed it; read it next to the audit "
            "problem rates below.", ""]

    # Runs
    if runs:
        live = [r for r in runs if not r.get("backfilled")]
        out += ["## Runs (meta/runs.jsonl)", "",
                f"- {len(runs)} runs ({len(runs) - len(live)} backfilled from git, {len(live)} logged live).", ""]
        if live:
            out += ["| prompt | model | runs | success | CI failures / run | review findings / run | integrity issues |",
                    "|---|---|---|---|---|---|---|"]
            groups = defaultdict(list)
            for r in live:
                groups[(r.get("prompt_version"), r.get("model"))].append(r)
            for (pv, model), rs in sorted(groups.items(), key=lambda kv: str(kv[0])):
                ok = sum(r.get("outcome") == "success" for r in rs)
                ci = [r["ci_failures_before_green"] for r in rs if isinstance(r.get("ci_failures_before_green"), int)]
                rv = [r["review_findings"] for r in rs if isinstance(r.get("review_findings"), int)]
                ii = sum(len(r.get("integrity_issues") or []) for r in rs)
                ci_s = f"{statistics.mean(ci):.2f}" if ci else "n/a"
                rv_s = f"{statistics.mean(rv):.2f}" if rv else "n/a"
                out.append(f"| {pv} | {model} | {len(rs)} | {pct(ok, len(rs))} | {ci_s} | {rv_s} | {ii} |")
            out.append("")

    # Audits
    if audits:
        out += ["## Audits (meta/audits.jsonl)", "", "| kind | projects audited | items checked | problems | rate |", "|---|---|---|---|---|"]
        by = defaultdict(list)
        for a in audits:
            by[a["kind"]].append(a)
        for kind, rows in sorted(by.items()):
            n, k = sum(a["checked"] for a in rows), sum(a["problems"] for a in rows)
            out.append(f"| {kind} | {len({a['slug'] for a in rows})} | {n} | {k} | {pct(k, n)} |")
        kinds = Counter(f["kind"] for a in audits for f in a.get("findings") or [])
        fixed = sum(bool(f.get("fixed")) for a in audits for f in a.get("findings") or [])
        total = sum(kinds.values())
        if total:
            out += ["", f"Findings by kind ({fixed} of {total} fixed): " +
                    ", ".join(f"{k} {n}" for k, n in kinds.most_common()) + "."]
        scores = [a["score"] for a in audits if isinstance(a.get("score"), (int, float))]
        if scores:
            out += [f"Reviewer score (1–5, would it impress a faculty reviewer): mean {statistics.mean(scores):.1f} "
                    f"over {len(scores)} projects."]
        out.append("")

    # Open debt from the static checks
    sys.path.insert(0, str(ROOT / "tools"))
    import check  # noqa: E402
    slugs = check.slugs()
    num = sum(bool(check.check_numbers(s)) for s in slugs)
    cit = sum(len(check.check_citations(s)) for s in slugs)
    out += ["## Open debt (tools/check.py warnings)", "",
            f"- Projects with a number in README or paper that no experiment prints: {pct(num, len(slugs))}.",
            f"- Reference-list entries never cited in the text: {cit}.",
            f"- Near-duplicate slugs: {len(check.duplicate_pairs(slugs))}.", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--backfill", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if git("rev-parse", "--is-shallow-repository").strip() == "true":
        print("warning: shallow clone; history-based numbers are incomplete (git fetch --unshallow)", file=sys.stderr)
    if args.check:
        errs = validate()
        for e in errs:
            print(f"ERROR: {e}")
        if errs:
            sys.exit(1)
    if args.backfill:
        print(f"backfilled {backfill(commits())} runs", file=sys.stderr)
    text = report()
    print(text)
    if args.write:
        REPORT.write_text(text + "\n")


if __name__ == "__main__":
    main()
