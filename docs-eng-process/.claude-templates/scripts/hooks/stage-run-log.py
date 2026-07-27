#!/usr/bin/env python3
"""
stage-run-log.py — OpenUP hook: fires BEFORE every Bash tool call (T-140).

When the command about to run is a `git commit`, this drains the untracked
run-log queue (`<main-repo-root>/.openup/run-log-pending.jsonl`) into each
record's own lane shard (`docs/agent-logs/runs/<UTC-date>-<lane-key>.jsonl`) and
`git add`s the touched shards — so the records land INSIDE the commit that is
about to be created.

Why a queue at all: a commit can never contain its own log record, because the
record carries the commit's SHA and the SHA hashes the tree that would hold it.
`auto-log-commit.py` (PostToolUse) can therefore only ever observe a commit
after the fact. Before T-140 it wrote straight into docs/agent-logs/, leaving
the tree dirty and forcing a follow-up "sweep" commit on every lane. Splitting
the write — observe post-commit, persist pre-next-commit — keeps the tree clean
and costs a steady-state lag of exactly one record.

Skipped deliberately:
  - a pathspec-limited commit (`git commit -- <paths>`), where a staged shard
    would be left staged-but-uncommitted — the very dirty tree this removes;
  - any command that is not a `git commit`.

All drain logic lives in `scripts/openup-runlog.py` so it is unit-testable
without a hook harness.

Exit codes:
  0 — always (this hook must never block or delay a commit)

Fail-open: any internal error is swallowed; a logging bug must never break the
user's session.

Hook event: PreToolUse / Bash
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

COMMIT_RE = re.compile(r"\bgit\b.*\bcommit\b", re.DOTALL)


def run(argv, cwd):
    try:
        r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
        return r.returncode, r.stdout.strip()
    except Exception:
        return 1, ""


def _worktree_heads(cwd: str) -> list[str]:
    """Paths of every linked worktree, main first. Empty on any failure."""
    rc, out = run(["git", "worktree", "list", "--porcelain"], cwd)
    if rc != 0 or not out:
        return []
    return [ln[len("worktree "):].strip()
            for ln in out.splitlines() if ln.startswith("worktree ")]


def target_worktree(cwd: str, command: str) -> str:
    """The worktree this commit will land in.

    OpenUP skills run `cd <worktree> && git commit` while the harness cwd stays
    pinned to the main checkout, so `payload.cwd` is not reliable. Prefer a
    worktree path that literally appears in the command; else fall back to the
    worktree holding an active .openup/state.json; else cwd (the plain
    no-worktree repo — today's behavior exactly).
    """
    heads = _worktree_heads(cwd)
    for path in heads:
        if path != cwd and path in command:
            return path
    if (Path(cwd) / ".openup" / "state.json").exists():
        return cwd
    for path in heads:
        if (Path(path) / ".openup" / "state.json").exists():
            return path
    return cwd


def main() -> None:
    try:
        raw = sys.stdin.read().strip()
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {}

        if payload.get("tool_name", "") != "Bash":
            sys.exit(0)

        command = payload.get("tool_input", {}).get("command", "")
        if not COMMIT_RE.search(command):
            sys.exit(0)

        cwd = payload.get("cwd", os.getcwd())
        worktree = target_worktree(cwd, command)

        script = Path(worktree) / "scripts" / "openup-runlog.py"
        if not script.exists():
            script = Path(cwd) / "scripts" / "openup-runlog.py"
        if not script.exists():
            sys.exit(0)

        # openup-runlog.py owns the pathspec guard, routing, dedupe and staging.
        run(["python3", str(script), "--cwd", worktree, "flush",
             "--worktree", worktree, "--command", command], worktree)

        sys.exit(0)

    except SystemExit:
        raise
    except Exception:
        sys.exit(0)  # fail open


if __name__ == "__main__":
    main()
