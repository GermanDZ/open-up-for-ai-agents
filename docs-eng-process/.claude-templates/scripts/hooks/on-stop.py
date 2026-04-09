#!/usr/bin/env python3
"""
on-stop.py — OpenUP hook: fires when the agent tries to stop.

Checks for uncommitted work and warns (or blocks) if the session would end
with files left behind. Implements the "End-of-Run Enforcement" pattern.

Exit codes:
  0 — all clear, stop proceeds normally
  2 — uncommitted work found; Claude continues and sees the message on stderr

Hook event: Stop
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def run(cmd: str, cwd: str) -> tuple[int, str]:
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True
    )
    return result.returncode, result.stdout.strip()


def main() -> None:
    raw = sys.stdin.read().strip()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {}

    cwd = payload.get("cwd", os.getcwd())

    # 1. Check for uncommitted changes
    _, dirty = run("git status --porcelain", cwd)
    if dirty:
        lines = dirty.splitlines()
        file_list = "\n".join(f"  {l}" for l in lines[:10])
        extra = f"\n  ... and {len(lines) - 10} more" if len(lines) > 10 else ""
        print(
            f"[on-stop] ⚠️  UNCOMMITTED CHANGES — do not stop yet.\n\n"
            f"The following files have uncommitted changes:\n{file_list}{extra}\n\n"
            f"Please commit or stash these changes before stopping.\n"
            f"Use the canonical format: type(scope): description [T-XXX]",
            file=sys.stderr,
        )
        sys.exit(2)

    # 2. Check: are we on trunk with commits that were never pushed/PR'd?
    # Only warn — not block — since this could be intentional
    _, trunk = run(
        "git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo main",
        cwd,
    )
    trunk = trunk or "main"
    _, current_branch = run("git rev-parse --abbrev-ref HEAD", cwd)

    if current_branch in ("main", "master", trunk):
        _, unpushed = run(f"git log origin/{trunk}..HEAD --oneline 2>/dev/null", cwd)
        if unpushed:
            print(
                f"[on-stop] ⚠️  On trunk ({current_branch}) with unpushed commits.\n"
                f"Consider pushing or creating a PR before ending the session:\n"
                + "\n".join(f"  {l}" for l in unpushed.splitlines()),
                file=sys.stderr,
            )
            # Don't block — staying on trunk can be intentional
            sys.exit(0)

    # All clear
    sys.exit(0)


if __name__ == "__main__":
    main()
