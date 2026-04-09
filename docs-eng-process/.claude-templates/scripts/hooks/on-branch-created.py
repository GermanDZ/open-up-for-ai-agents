#!/usr/bin/env python3
"""
on-branch-created.py — OpenUP hook: fires after every Bash tool call.

Detects when a new task branch is created (git checkout -b) in an OpenUP
project and reminds Claude to deploy the team if it hasn't done so yet.

The team must be deployed BEFORE any implementation work begins. This hook
fires immediately after branch creation to enforce that order.

Exit codes:
  0 — not a branch creation, OR not an OpenUP project, OR reminder sent (always 0)

Note: PostToolUse hooks cannot block (exit 2 is not supported). This hook
uses exit 0 and prints to stderr so Claude sees the reminder and acts on it.

Hook event: PostToolUse / Bash
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Detect `git checkout -b <branch>` or `git switch -c <branch>`
BRANCH_CREATE_RE = re.compile(
    r"\bgit\b.+(?:checkout\s+-[cCbB]|switch\s+-[cC])\s+(\S+)",
    re.DOTALL,
)

# OpenUP task branch prefixes — ignore utility branches
TASK_BRANCH_RE = re.compile(
    r"^(feature|feat|fix|bugfix|hotfix|refactor|task|chore|docs|test|quick|inception|elaboration|construction|transition)/",
)


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

    if payload.get("tool_name", "") != "Bash":
        sys.exit(0)

    command = payload.get("tool_input", {}).get("command", "")

    # Only act on branch creation commands
    m = BRANCH_CREATE_RE.search(command)
    if not m:
        sys.exit(0)

    branch_name = m.group(1).strip()

    # Only care about OpenUP task branches
    if not TASK_BRANCH_RE.match(branch_name):
        sys.exit(0)

    cwd = payload.get("cwd", os.getcwd())

    # Only act on OpenUP-managed projects
    if not (Path(cwd) / "docs" / "project-status.md").exists():
        sys.exit(0)

    # Determine phase for team suggestion
    status_path = Path(cwd) / "docs" / "project-status.md"
    phase = "construction"
    try:
        for line in status_path.read_text().splitlines():
            m2 = re.match(r"\*\*Phase\*\*:\s*(.+)", line, re.IGNORECASE)
            if m2:
                phase = m2.group(1).strip().lower()
                break
    except OSError:
        pass

    phase_team_map = {
        "inception": "openup-inception-team (analyst + project-manager)",
        "elaboration": "openup-elaboration-team (architect + developer)",
        "construction": "openup-construction-team (developer + tester)",
        "transition": "openup-transition-team (developer + tester + project-manager)",
    }
    suggested_team = phase_team_map.get(phase, "openup-construction-team (developer + tester)")

    print(
        f"[on-branch-created] ✅ Branch '{branch_name}' created.\n\n"
        f"⛔ STOP — deploy the team NOW before writing any code or modifying any files.\n\n"
        f"Current phase: {phase}\n"
        f"Suggested team: {suggested_team}\n\n"
        f"Deploy using the Agent tool:\n"
        f"  - Spawn each role with the iteration goal, task ID, and relevant docs\n"
        f"  - Brief the project-manager as coordinator (decompose → delegate → synthesize)\n"
        f"  - Specialists (developer, architect, tester) receive focused subtasks from the PM\n\n"
        f"Only after the team is deployed should implementation work begin.",
        file=sys.stderr,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
