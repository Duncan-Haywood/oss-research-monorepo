#!/usr/bin/env python3
"""UserPromptSubmit hook: save every prompt sent to an agent, verbatim, in git.

Claude Code passes the hook a JSON object on stdin with `session_id` and
`prompt`. Each session gets its own file, so parallel sessions never conflict:
    .claude/prompts/<YYYY-MM-DD>/<session_id>.md
Agents commit these files along with their work (see CLAUDE.md).

Strings that look like credentials are masked before anything is written,
because this repository is public.
"""
import datetime
import json
import os
import re
import sys

SECRET_RE = re.compile(
    r"(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}"
    r"|AKIA[0-9A-Z]{16}|xox[abpr]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return  # never block a prompt because logging failed
    prompt = data.get("prompt") or ""
    session = re.sub(r"[^A-Za-z0-9_-]", "", data.get("session_id") or "unknown")
    now = datetime.datetime.now(datetime.timezone.utc)
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or "."
    folder = os.path.join(root, ".claude", "prompts", now.strftime("%Y-%m-%d"))
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, session + ".md")
    new = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as f:
        if new:
            f.write(f"# Prompts for session {session}\n")
            remote = os.environ.get("CLAUDE_CODE_REMOTE_SESSION_ID")
            if remote:
                f.write(f"\nRemote session: https://claude.ai/code/{remote}\n")
        f.write(f"\n## {now.strftime('%Y-%m-%dT%H:%M:%SZ')}\n\n")
        f.write(SECRET_RE.sub("[REDACTED]", prompt).rstrip() + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # logging must never stop the agent from receiving the prompt
