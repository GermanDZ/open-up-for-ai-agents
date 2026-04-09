#!/usr/bin/env python3
"""
check-iteration.py — OpenUP hook: fires before every Bash tool call.

Intercepts `git commit` commands and verifies the agent is working inside an
active OpenUP iteration before allowing the commit.

An "active iteration" requires ALL of:
  1. docs/project-status.md exists (project is OpenUP-managed)
  2. **Status** field is "in-progress"
  3. **Current Task** is not "None" / empty
  4. Current git branch is NOT trunk (main/master)

If any condition is violated the commit is blocked and Claude is told exactly
what to run to initialize the iteration and re-create the missing docs entries.

Exit codes:
  0 — not a git commit, OR project not OpenUP-managed, OR iteration is active
  2 — iteration missing — block with recovery instructions on stderr

Hook event: PreToolUse / Bash
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Patterns for command filtering (shared with validate-commit.py)
COMMIT_RE = re.compile(r"\bgit\b.*\bcommit\b", re.DOTALL)
MSG_FLAG_RE = re.compile(r"(?:-m|--message)\s", re.DOTALL)


def run(cmd: str, cwd: str) -> tuple[int, str]:
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True
    )
    return result.returncode, result.stdout.strip()


def get_trunk(cwd: str) -> str:
    _, trunk = run(
        "git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null "
        "| sed 's@^refs/remotes/origin/@@'",
        cwd,
    )
    trunk = trunk.strip()
    if trunk:
        return trunk
    # Local-only repo: check which of main/master exists
    _, branches = run("git branch", cwd)
    for line in branches.splitlines():
        b = line.strip().lstrip("* ")
        if b in ("main", "master"):
            return b
    return "main"


def parse_project_status(path: Path) -> dict[str, str]:
    """Extract **Key**: value pairs from project-status.md."""
    fields: dict[str, str] = {}
    try:
        text = path.read_text()
    except OSError:
        return fields
    for line in text.splitlines():
        m = re.match(r"\*\*(.+?)\*\*:\s*(.*)", line)
        if m:
            fields[m.group(1).strip()] = m.group(2).strip()
    return fields


def main() -> None:
    raw = sys.stdin.read().strip()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {}

    if payload.get("tool_name", "") != "Bash":
        sys.exit(0)

    command = payload.get("tool_input", {}).get("command", "")

    # Only act on git commit commands
    if not COMMIT_RE.search(command):
        sys.exit(0)

    # Skip --amend without -m (reuses existing message — not a new commit context)
    if "--amend" in command and not MSG_FLAG_RE.search(command):
        sys.exit(0)

    # Skip --allow-empty-message
    if "--allow-empty-message" in command:
        sys.exit(0)

    cwd = payload.get("cwd", os.getcwd())

    # ── Is this an OpenUP project? ──────────────────────────────────────────
    status_path = Path(cwd) / "docs" / "project-status.md"
    if not status_path.exists():
        sys.exit(0)  # Not OpenUP-managed — let it through

    # ── Parse project status ─────────────────────────────────────────────────
    fields = parse_project_status(status_path)
    status = fields.get("Status", "").lower()
    current_task = fields.get("Current Task", "None").strip()

    # ── Check git branch ─────────────────────────────────────────────────────
    _, branch = run("git rev-parse --abbrev-ref HEAD", cwd)
    trunk = get_trunk(cwd)
    on_trunk = branch in ("main", "master", trunk)

    # ── Evaluate iteration health ─────────────────────────────────────────────
    status_ok = status == "in-progress"
    task_ok = current_task not in ("", "None", "none", "-")
    branch_ok = not on_trunk

    if status_ok and task_ok and branch_ok:
        sys.exit(0)  # All clear — active iteration on task branch

    # ── Build diagnosis ───────────────────────────────────────────────────────
    issues: list[str] = []
    if on_trunk:
        issues.append(
            f"  ❌ On trunk branch '{branch}' — work must happen on a task branch"
        )
    if not status_ok:
        label = status if status else "unknown"
        issues.append(
            f"  ❌ Project status is '{label}' (expected 'in-progress')"
        )
    if not task_ok:
        issues.append(
            f"  ❌ No current task assigned (Current Task: {current_task})"
        )

    issues_text = "\n".join(issues)

    print(
        f"[check-iteration] ❌ No active OpenUP iteration — commit blocked.\n\n"
        f"Issues found:\n{issues_text}\n\n"
        f"Initialize an iteration first, then retry the commit:\n\n"
        f"  For full task work (new feature, bug fix, refactor):\n"
        f"    /openup-start-iteration task_id: T-XXX\n\n"
        f"  For small changes (docs, config, quick fixes < 50 lines):\n"
        f"    /openup-quick-task task: \"brief description of what you did\"\n\n"
        f"Initializing will:\n"
        f"  • Create a task branch (branching off trunk)\n"
        f"  • Update docs/project-status.md with the active iteration + task\n"
        f"  • Log the run start in docs/agent-logs/agent-runs.jsonl\n"
        f"  • Assign a task ID for traceability\n\n"
        f"If this task is not yet in the roadmap, add it first:\n"
        f"    /openup-plan-feature\n"
        f"  or manually add a T-XXX entry to docs/roadmap.md.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
