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
  run log     (with --changed) a change under research/ appends a line to meta/runs.jsonl

With --changed, the heuristic checks (numbers, citations, duplicates) are errors for new projects and for the lines
the change adds, and warnings elsewhere, so old debt stays visible without blocking unrelated work; experiments are
re-run for new projects and for projects whose src/, experiments/ or tests/ changed. Exits 1 on any error.
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
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

def _source_values(slug):
    d = RESEARCH / slug / "experiments"
    text = "".join(f.read_text(errors="ignore") for f in sorted(d.glob("*.txt")) + sorted(d.glob("*.py"))) if d.exists() else ""
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)  # 2,155,728 -> 2155728
    vals = []
    for tok in re.findall(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text):
        try:
            vals.append(abs(float(tok)))
        except ValueError:
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
    if tok in text:
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


def check_numbers(slug):
    text, vals = _source_values(slug)
    if not text:
        return []
    out = []
    for doc in filter(None, [RESEARCH / slug / "README.md", paper_path(slug)]):
        rel = str(doc.relative_to(RESEARCH / slug))
        for line in strip_references(doc.read_text()).splitlines():
            if SKIP_LINE.search(line):
                continue
            for tok in DECIMAL.findall(line):
                if not _traced(tok, text, vals):
                    out.append((rel, line.strip(), f"{rel}: {tok} not found in experiments/ output or code"))
    return list(dict.fromkeys(out))


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
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, "experiments/run.py"], cwd=d, env=_env(), capture_output=True, text=True,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return slug, False, time.time() - t0, f"timed out after {timeout} s"
    if r.returncode != 0:
        return slug, False, time.time() - t0, r.stderr[-1500:]
    want = res.read_text()
    if r.stdout == want:
        return slug, True, time.time() - t0, ""
    diff = next((f"line {i + 1}: committed {a!r} vs re-run {b!r}"
                 for i, (a, b) in enumerate(zip(want.splitlines(), r.stdout.splitlines())) if a != b),
                "output length differs")
    return slug, False, time.time() - t0, diff


# ---- changed projects and run log --------------------------------------------------------------

def changed_since(ref):
    """Files changed since ref; per project, the lines added to each file; new projects; projects whose code changed."""
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    files = git("diff", "--name-only", f"{ref}...HEAD").split()
    added, path = {}, None
    for line in git("diff", "-U0", f"{ref}...HEAD", "--", "research/").splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif path and path.count("/") >= 2 and line.startswith("+") and not line.startswith("+++"):
            _, slug, rel = path.split("/", 2)
            added.setdefault(slug, {}).setdefault(rel, set()).add(line[1:].strip())
    touched = {f.split("/")[1] for f in files if f.startswith("research/") and f.count("/") >= 2}
    new = {s for s in touched if subprocess.run(["git", "cat-file", "-e", f"{ref}:research/{s}"], cwd=ROOT,
                                                capture_output=True).returncode != 0}
    code = {f.split("/")[1] for f in files if re.match(r"research/[^/]+/(src|experiments|tests)/", f)}
    return files, added, new, code


def check_run_log(ref, files):
    if not any(f.startswith("research/") for f in files):
        return []
    log = ROOT / "meta" / "runs.jsonl"
    old = subprocess.run(["git", "show", f"{ref}:meta/runs.jsonl"], cwd=ROOT, capture_output=True, text=True).stdout
    new = log.read_text() if log.exists() else ""
    added = [l for l in new.splitlines()[len(old.splitlines()):] if l.strip()]
    errs = []
    if not new.startswith(old):
        errs.append("meta/runs.jsonl: existing lines were edited; only append (add a correction line instead)")
    if not added:
        errs.append("meta/runs.jsonl: this change touches research/ but appends no run line (see prompt.md, Run log)")
    for l in added:
        try:
            rec = json.loads(l)
        except json.JSONDecodeError as e:
            errs.append(f"meta/runs.jsonl: bad JSON in appended line ({e})")
            continue
        missing = [k for k in ("date", "session", "prompt_version", "model", "task", "outcome", "projects") if k not in rec]
        if missing:
            errs.append(f"meta/runs.jsonl: appended line lacks {', '.join(missing)}")
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
    files, added, new, code = [], {}, set(), set()
    if args.changed:
        files, added, new, code = changed_since(args.changed)
        new, code = new & set(all_slugs), code & set(all_slugs)
    strict = new | code | {s for s in added if s in all_slugs}
    errors, warnings = [], []

    for s in targets:
        errors += [f"{s}: {e}" for e in check_layout(s) + check_disclosure(s)]
        for name, fn in (("numbers", check_numbers), ("citations", check_citations)):
            for rel, line, msg in fn(s):
                # Strict on new projects and on lines this change adds; old debt elsewhere is a warning.
                hard = s in new or line in added.get(s, {}).get(rel, ())
                (errors if hard else warnings).append(f"{s}: [{name}] {msg}")
    for a, b in duplicate_pairs(all_slugs):
        msg = f"{a} and {b}: near-duplicate slugs; merge them or rename one to say how it differs"
        (errors if new & {a, b} else warnings).append(msg)
    if args.changed:
        errors += check_run_log(args.changed, files)

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
