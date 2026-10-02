"""Programmatic checks for every project under research/.

    python tools/check.py                         # every check on every project (unit tests included)
    python tools/check.py --changed origin/main   # strict on projects changed since the ref, and re-run their experiments
    python tools/check.py --repro SLUG [SLUG ...] # re-run experiments/run.py and diff stdout against experiments/results.txt
    python tools/check.py --repro-sample 12       # re-run a random sample (the weekly audit); --seed fixes the draw
    python tools/check.py --no-tests              # skip the unit tests

Checks, per project:
  layout      README.md, tests, experiments/run.py, experiments/results.txt, paper/whitepaper.md
  disclosure  the paper (or README if there is no paper) states it was produced with AI assistance
  tests       unittest discovery passes, with every research/*/src on PYTHONPATH
  numbers     every decimal in README.md and the paper traces to experiments/results.txt or run.py
  citations   every entry under "## References" is cited in the text of the paper
  duplicates  no two slugs are the same once hyphens are removed
  repro       (on request) experiments/run.py reproduces experiments/results.txt byte for byte
  run log     (with --changed) a change under research/ adds or updates meta/runs/<session-id>.json

With --changed (compared against the merge-base), the heuristic checks (numbers, citations, duplicates) are errors
for new projects and for the lines the change adds, and warnings elsewhere, so old debt stays visible without blocking
unrelated work. For projects whose src/, experiments/ or tests/ changed, experiments are re-run and a number that
traced before the change but no longer does is an error. A renamed project is not new. Exits 1 on any error.
Numbers: only decimals are checked (integers and percentages are not), after labels such as "Section 4.3" are skipped.
"""
import argparse
import io
import json
import os
import random
import re
import subprocess
import sys
import time
import tokenize
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "research"

# Projects written before the standard layout existed. Each entry says what is missing and why;
# shrink this list, never grow it.
# Their long READMEs are the write-up; a whitepaper would duplicate them.
LEGACY = {
    "decentralized-verification-markets": {"paper"},
    "property-elicitation-verification": {"paper"},
    "wagering-modular-experts": {"paper"},
}

DISCLOSURE = re.compile(r"AI assistance", re.I)
DECIMAL = re.compile(r"(?<![\w.\-/])-?\d+\.\d+(?:\s*[·×x*]\s*10\^?[⁻\-−]?[⁰¹²³⁴⁵⁶⁷⁸⁹\d]+|[eE][-+]?\d+)?(?![\w.])")
SUPERSCRIPT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻−", "0123456789--")
SKIP_LINE = re.compile(r"arxiv|doi|https?://|\bpp?\.\s|\(\d{4}\)\.|^\s*python3? |PYTHONPATH", re.I)
# A decimal right after one of these is a label ("Section 4.3", "Prop. 2.1"), not a result.
LABEL = re.compile(r"(?:section|sec\.|§|proposition|prop\.|theorem|lemma|corollary|definition|eqs?\.|equation|"
                   r"fig\.|figure|table|appendix|algorithm|step|v)\s*$", re.I)


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=check).stdout


def slugs():
    return sorted(p.name for p in RESEARCH.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))


def paper_path(slug):
    p = RESEARCH / slug / "paper" / "whitepaper.md"
    return p if p.exists() else None


def strip_references(text):
    return re.split(r"^#+\s*(References|Bibliography)\b", text, flags=re.M | re.I)[0]


# ---- layout and disclosure -------------------------------------------------------------------

def check_layout(slug):
    d, exempt, errs = RESEARCH / slug, LEGACY.get(slug, set()), []
    if not (d / "README.md").exists():
        errs.append("no README.md")
    if not any(re.search(r"^\s*def test_", f.read_text(errors="ignore"), re.M) for f in d.rglob("test*.py")):
        errs.append("no unit tests (def test_ in test*.py)")
    for key, rel in (("run.py", "experiments/run.py"), ("results", "experiments/results.txt"),
                     ("paper", "paper/whitepaper.md")):
        if key not in exempt and not (d / rel).exists():
            errs.append(f"no {rel}")
    for key in exempt:
        rel = {"run.py": "experiments/run.py", "results": "experiments/results.txt", "paper": "paper/whitepaper.md"}[key]
        if (d / rel).exists():
            errs.append(f"{rel} now exists: remove '{key}' from LEGACY in tools/check.py")
    return errs


def check_disclosure(slug):
    target = paper_path(slug) or RESEARCH / slug / "README.md"
    if target.exists() and not DISCLOSURE.search(target.read_text()):
        return [f"{target.relative_to(ROOT)} does not state that it was produced with AI assistance"]
    return []


# ---- numbers ---------------------------------------------------------------------------------

def _read(slug, rel, rev=None):
    """A project file's text in the working tree, or at git revision rev; '' if absent."""
    if rev is None:
        f = RESEARCH / slug / rel
        return f.read_text(errors="ignore") if f.exists() else ""
    return git("show", f"{rev}:research/{slug}/{rel}", check=False)


def _experiment_files(slug, rev=None):
    if rev is None:
        d = RESEARCH / slug / "experiments"
        return sorted(f.name for f in d.iterdir() if f.is_file()) if d.exists() else []
    out = git("ls-tree", "--name-only", f"{rev}:research/{slug}/experiments", check=False)
    return sorted(out.split())


def _source_values(slug, rev=None):
    """Printed output (experiments/*.txt) as text, plus every number in it and every numeric literal in
    experiments/*.py code (comments and docstrings excluded)."""
    names = _experiment_files(slug, rev)
    text = "".join(_read(slug, f"experiments/{n}", rev) for n in names if n.endswith(".txt"))
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)  # 2,155,728 -> 2155728
    vals = []
    for tok in re.findall(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text):
        vals.append(abs(float(tok)))
    for n in names:
        if n.endswith(".py"):
            try:
                for t in tokenize.generate_tokens(io.StringIO(_read(slug, f"experiments/{n}", rev)).readline):
                    if t.type == tokenize.NUMBER:
                        try:
                            vals.append(abs(float(t.string.replace("_", ""))))
                        except ValueError:
                            pass
            except (tokenize.TokenError, IndentationError, SyntaxError):
                pass
    return text, vals


def _parse(tok):
    """'7.3·10⁻⁴' -> (0.00073, relative tolerance); '0.930' -> (0.93, absolute half-ulp of the printed digits)."""
    m = re.match(r"(-?\d+\.(\d+))(?:\s*[·×x*]\s*10\^?(.+)|[eE]([-+]?\d+))?$", tok)
    mant, digits, exp = float(m.group(1)), len(m.group(2)), m.group(3) or m.group(4)
    if exp is None:
        return abs(mant), None, digits
    e = int(exp.translate(SUPERSCRIPT))
    return abs(mant) * 10 ** e, 0.5 * 10 ** -digits / max(abs(mant), 1e-300), digits


def _traced(tok, text, vals):
    if re.search(r"(?<![\d.])" + re.escape(tok) + r"(?!\d)", text):
        return True
    v, rel, dp = _parse(tok)
    if rel is not None:
        return any(f and abs(f - v) <= rel * v * 1.0001 for f in vals)
    target = round(v, dp)
    for f in vals:
        for scale in (1, 100, 1000, 0.01, 0.001, 1e6, 1e-6):
            if abs(round(f * scale, dp) - target) < 10 ** -(dp + 3) or abs(f * scale - v) <= 0.5 * 10 ** -dp + 1e-12:
                return True
    return False


def check_numbers(slug, rev=None):
    """Decimals in README.md and the paper that no experiment output or code value accounts for.
    Returns (file, line, token, message) tuples."""
    text, vals = _source_values(slug, rev)
    if not text and not vals:
        return []
    out = []
    for rel in ("README.md", "paper/whitepaper.md"):
        for line in strip_references(_read(slug, rel, rev)).splitlines():
            if SKIP_LINE.search(line):
                continue
            for m in DECIMAL.finditer(line):
                tok = m.group(0)
                if LABEL.search(line[:m.start()]) or _traced(tok, text, vals):
                    continue
                out.append((rel, line.strip(), tok, f"{rel}: {tok} not found in experiments/ output or code"))
    return list(dict.fromkeys(out))


def number_regressions(slug, base):
    """Numbers in the write-up that traced at base and no longer do: the code changed under the text."""
    before = {(rel, tok) for rel, _, tok, _ in check_numbers(slug, base)}
    docs = {rel: _read(slug, rel, base) for rel in ("README.md", "paper/whitepaper.md")}
    return [x for x in check_numbers(slug) if (x[0], x[2]) not in before and x[2] in docs[x[0]]]


# ---- citations -------------------------------------------------------------------------------

def check_citations(slug):
    p = paper_path(slug)
    if not p:
        return []
    text = p.read_text()
    parts = re.split(r"^#+\s*(?:References|Bibliography)\b.*$", text, flags=re.M | re.I)
    if len(parts) < 2:
        return []
    body, refs = parts[0], re.split(r"^#+\s", parts[1], flags=re.M)[0]
    out = []
    for full, entry in re.findall(r"^(\s*[-*]\s+(.+))$", refs, re.M):
        label = re.match(r"\[([^\]]+)\]", entry)
        if label and re.search(r"\[[^\]]*(?<![\w-])" + re.escape(label.group(1)) + r"(?![\w-])[^\]]*\]", body):
            continue
        m = re.match(r"(?:\[[^\]]*\]\s*)?([^\s,.(]+(?:\s(?:de|van|der|von|da|di|la|le)\s?[^\s,.(]+)*)", entry)
        if not m:
            continue
        surname = m.group(1).strip("*_")
        if len(surname) > 2 and surname.lower() not in body.lower():
            out.append(("paper/whitepaper.md", full.strip(),
                        f"paper/whitepaper.md: reference '{entry[:60]}' is never cited in the text"))
    return out


# ---- duplicates ------------------------------------------------------------------------------

def duplicate_pairs(all_slugs):
    seen, pairs = {}, []
    for s in all_slugs:
        key = s.replace("-", "")
        if key in seen:
            pairs.append((seen[key], s))
        seen[key] = s
    return pairs


# ---- unit tests and reproduction -------------------------------------------------------------

def _env():
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(["src", "."] + [str(p) for p in sorted(RESEARCH.glob("*/src"))])
    env["PYTHONHASHSEED"] = "0"
    return env


def run_tests(slug):
    d = RESEARCH / slug
    start = d / "tests" if (d / "tests").is_dir() else d
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(start), "-t", str(start), "-p", "test*.py"],
                           cwd=d, env=_env(), capture_output=True, text=True, timeout=1200)
    except subprocess.TimeoutExpired:
        return slug, False, 0, time.time() - t0, "timed out after 1200 s"
    m = re.search(r"^Ran (\d+) tests?", r.stderr, re.M)
    n = int(m.group(1)) if m else 0
    ok = r.returncode == 0 and n > 0
    return slug, ok, n, time.time() - t0, "" if ok else (r.stderr[-1500:] or "no tests ran")


def run_repro(slug, timeout=1800):
    d = RESEARCH / slug
    run, res = d / "experiments" / "run.py", d / "experiments" / "results.txt"
    if not (run.exists() and res.exists()):
        return slug, None, 0.0, "no experiments/run.py + results.txt pair"
    want, mtime = res.read_text(), res.stat().st_mtime_ns
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, "experiments/run.py"], cwd=d, env=_env(), capture_output=True, text=True,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return slug, False, time.time() - t0, f"timed out after {timeout} s"
    finally:
        # Some run.py scripts write results.txt themselves: take what they wrote, then restore the committed file.
        wrote = res.exists() and res.stat().st_mtime_ns != mtime
        got_file = res.read_text() if wrote else None
        if wrote:
            res.write_text(want)
    if r.returncode != 0:
        return slug, False, time.time() - t0, r.stderr[-1500:]
    got = got_file if wrote else r.stdout
    if got == want:
        return slug, True, time.time() - t0, ""
    diff = next((f"line {i + 1}: committed {a!r} vs re-run {b!r}"
                 for i, (a, b) in enumerate(zip(want.splitlines(), got.splitlines())) if a != b),
                "output length differs")
    return slug, False, time.time() - t0, diff


# ---- changed projects and run log --------------------------------------------------------------

RUN_KEYS = ("date", "session", "prompt_version", "model", "task", "outcome", "projects")


def changed_since(ref):
    """Against the merge-base of ref and HEAD: changed files with status, the lines added per project file,
    new projects (renames map back to their old slug), projects whose code changed, and the base itself."""
    base = git("merge-base", ref, "HEAD").strip()
    status, renamed = {}, {}
    for line in git("diff", "--name-status", "-M", base, "HEAD").splitlines():
        parts = line.split("\t")
        status[parts[-1]] = parts[0][0]
        if parts[0].startswith("R") and parts[1].startswith("research/") and parts[2].startswith("research/"):
            renamed[parts[2].split("/")[1]] = parts[1].split("/")[1]
    added, path = {}, None
    for line in git("diff", "-U0", "-M", base, "HEAD", "--", "research/").splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif path and path.count("/") >= 2 and line.startswith("+") and not line.startswith("+++"):
            _, slug, rel = path.split("/", 2)
            added.setdefault(slug, {}).setdefault(rel, set()).add(line[1:].strip())
    touched = {f.split("/")[1] for f in status if f.startswith("research/") and f.count("/") >= 2}
    exists = lambda s: subprocess.run(["git", "cat-file", "-e", f"{base}:research/{s}"], cwd=ROOT,
                                      capture_output=True).returncode == 0
    new = {s for s in touched if not exists(renamed.get(s, s))}
    code = {f.split("/")[1] for f in status if re.match(r"research/[^/]+/(src|experiments|tests)/", f)}
    return status, added, new, code, base


def check_run_log(status):
    """A change under research/ adds or updates its run's record, meta/runs/<session-id>.json."""
    if not any(f.startswith("research/") for f in status):
        return []
    errs = []
    records = [f for f, st in status.items() if re.fullmatch(r"meta/runs/[^/]+\.json", f) and st in "AMR"]
    if not records:
        errs.append("meta/runs/: this change touches research/ but adds or updates no run record "
                    "(meta/runs/<session-id>.json; see prompt.md, Run log)")
    for f in [f for f, st in status.items() if f.startswith("meta/runs/") and st == "M" and f.endswith(".jsonl")]:
        errs.append(f"{f}: a historical log was edited; never edit other runs' records")
    for f in records:
        try:
            rec = json.loads((ROOT / f).read_text())
        except (json.JSONDecodeError, FileNotFoundError) as e:
            errs.append(f"{f}: not a JSON object ({e})")
            continue
        missing = [k for k in RUN_KEYS if k not in rec] if isinstance(rec, dict) else list(RUN_KEYS)
        if missing:
            errs.append(f"{f}: lacks {', '.join(missing)}")
    return errs


# ---- main ------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--changed", metavar="REF", help="be strict on projects changed since REF and re-run their experiments")
    ap.add_argument("--repro", nargs="*", default=[], metavar="SLUG", help="re-run these projects' experiments")
    ap.add_argument("--repro-sample", type=int, default=0, metavar="N", help="re-run N random projects' experiments")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--no-tests", action="store_true")
    ap.add_argument("--only", nargs="*", default=None, metavar="SLUG", help="restrict every check to these projects")
    ap.add_argument("--jobs", type=int, default=max(2, os.cpu_count() or 2))
    ap.add_argument("--json", metavar="FILE", help="also write the findings as JSON")
    args = ap.parse_args()

    all_slugs = slugs()
    targets = [s for s in all_slugs if args.only is None or s in args.only]
    status, added, new, code, base = {}, {}, set(), set(), None
    if args.changed:
        status, added, new, code, base = changed_since(args.changed)
        new, code = new & set(all_slugs), code & set(all_slugs)
    strict = new | code | {s for s in added if s in all_slugs}
    errors, warnings = [], []

    for s in targets:
        errors += [f"{s}: {e}" for e in check_layout(s) + check_disclosure(s)]
        for name, fn in (("numbers", check_numbers), ("citations", check_citations)):
            for rel, line, *_, msg in fn(s):
                # Strict on new projects and on lines this change adds; old debt elsewhere is a warning.
                hard = s in new or line in added.get(s, {}).get(rel, ())
                (errors if hard else warnings).append(f"{s}: [{name}] {msg}")
        if s in code - new:
            errors += [f"{s}: [numbers] {msg} (it traced before this change: re-run experiments/run.py or fix the text)"
                       for *_, msg in number_regressions(s, base)]
    for a, b in duplicate_pairs(all_slugs):
        msg = f"{a} and {b}: near-duplicate slugs; merge them or rename one to say how it differs"
        (errors if new & {a, b} else warnings).append(msg)
    if args.changed:
        errors += check_run_log(status)

    report = {"tests": {}, "repro": {}}
    with ThreadPoolExecutor(args.jobs) as pool:
        if not args.no_tests:
            t0 = time.time()
            for slug, ok, n, secs, msg in pool.map(run_tests, targets):
                report["tests"][slug] = {"ok": ok, "ran": n, "seconds": round(secs, 1)}
                if not ok:
                    errors.append(f"{slug}: unit tests failed\n{msg}")
            ran = sum(v["ran"] for v in report["tests"].values())
            print(f"tests: {ran} in {len(targets)} projects, {time.time() - t0:.0f} s")
        repro = set(args.repro) | new | code
        if args.repro_sample:
            pool_slugs = [s for s in all_slugs if (RESEARCH / s / "experiments" / "run.py").exists()
                          and (RESEARCH / s / "experiments" / "results.txt").exists()]
            seed = args.seed if args.seed is not None else random.SystemRandom().randrange(10 ** 6)
            repro |= set(random.Random(seed).sample(pool_slugs, min(args.repro_sample, len(pool_slugs))))
            print(f"repro sample: seed {seed}")
        for slug, ok, secs, msg in pool.map(run_repro, sorted(repro)):
            report["repro"][slug] = {"ok": ok, "seconds": round(secs, 1), "detail": msg}
            print(f"repro {slug}: {'identical' if ok else 'n/a' if ok is None else 'DIFFERS'} ({secs:.0f} s){'  ' + msg if ok is False else ''}")
            if ok is False:
                errors.append(f"{slug}: experiments/run.py does not reproduce experiments/results.txt: {msg}")
            elif ok is None and slug in new | code:
                errors.append(f"{slug}: {msg}")

    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"{len(targets)} projects, {len(strict)} changed, {len(errors)} errors, {len(warnings)} warnings")
    if args.json:
        Path(args.json).write_text(json.dumps({"errors": errors, "warnings": warnings, **report}, indent=1))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
