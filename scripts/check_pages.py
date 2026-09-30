"""Check that the GitHub Pages homepage and README list every research project.

Every directory under research/ must have a README bullet and a docs/index.html
entry, and neither may link to a project that no longer exists. Run from the
repo root: python scripts/check_pages.py
"""
import re
import sys
from pathlib import Path

REPO = "Duncan-Haywood/oss-research-monorepo"
ROOT = Path(__file__).resolve().parent.parent


def main():
    projects = {p.name for p in (ROOT / "research").iterdir() if p.is_dir()}
    readme = (ROOT / "README.md").read_text()
    page = (ROOT / "docs" / "index.html").read_text()

    in_readme = set(re.findall(r"^- \[`research/([\w-]+)`\]", readme, re.M))
    in_page = set(re.findall(r"github\.com/[\w-]+/[\w-]+/tree/main/research/([\w-]+)", page))
    bad_repo = sorted(set(re.findall(r"github\.com/([\w-]+/[\w-]+)/tree/", page)) - {REPO})

    errors = []
    for name, found in (("README.md", in_readme), ("docs/index.html", in_page)):
        errors += [f"{name}: missing entry for research/{p}" for p in sorted(projects - found)]
        errors += [f"{name}: entry for nonexistent research/{p}" for p in sorted(found - projects)]
    errors += [f"docs/index.html: links to {r}, expected {REPO}" for r in bad_repo]

    for e in errors:
        print(e)
    if errors:
        sys.exit(1)
    print(f"ok: {len(projects)} projects listed in README.md and docs/index.html")


if __name__ == "__main__":
    main()
