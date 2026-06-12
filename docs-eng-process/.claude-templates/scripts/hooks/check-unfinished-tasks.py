#!/usr/bin/env python3
"""
check-unfinished-tasks.py — OpenUP hook: fires on UserPromptSubmit.

When the user attempts to start a new iteration, checks whether there is
already unfinished work that should be completed or explicitly deferred first.

Triggers on prompts that contain iteration-start patterns:
  /openup-start-iteration, /openup-construction, /openup-elaboration,
  /openup-inception, /openup-transition

Checks (in order):
  1. docs/project-status.md — is an iteration already in-progress?
  2. docs/roadmap.md        — are any tasks marked in-progress?
  3. git status             — uncommitted changes on the current branch?
  4. git log               — unmerged commits on the current task branch?

Exit codes:
  0 — not a start-iteration prompt, OR project not OpenUP-managed, OR no issues
  2 — unfinished work found — block with recovery instructions on stderr

Hook event: UserPromptSubmit
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Prompt patterns that signal intent to start a new iteration
START_PATTERNS = re.compile(
    r"/openup-start-iteration"
    r"|/openup-construction"
    r"|/openup-elaboration"
    r"|/openup-inception"
    r"|/openup-transition",
    re.IGNORECASE,
)


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
    _, branches = run("git branch", cwd)
    for line in branches.splitlines():
        b = line.strip().lstrip("* ")
        if b in ("main", "master"):
            return b
    return "main"


def parse_project_status(path: Path) -> dict[str, str]:
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


def find_inprogress_tasks(roadmap_path: Path) -> list[str]:
    """
    Find all task IDs and titles where status is in-progress.

    Handles two roadmap formats:
      - Markdown table: | T-007 | title | ... | in-progress | ...
      - Detail section: **Status**: in-progress (preceded by ### T-007: title)
    """
    tasks: list[str] = []
    try:
        text = roadmap_path.read_text()
    except OSError:
        return tasks

    lines = text.splitlines()
    current_heading: str | None = None

    for line in lines:
        # Track ### T-XXX: title headings
        h = re.match(r"^###\s+(T-\w+):\s*(.+)", line)
        if h:
            current_heading = f"{h.group(1)}: {h.group(2).strip()}"
            continue

        # Detail section status line
        m = re.match(r"\*\*Status\*\*:\s*(.+)", line)
        if m and m.group(1).strip().lower() == "in-progress" and current_heading:
            tasks.append(current_heading)
            current_heading = None
            continue

        # Table row: | T-XXX | title | ... | in-progress | ...
        if "|" in line and "in-progress" in line.lower():
            cols = [c.strip() for c in line.split("|") if c.strip()]
            if len(cols) >= 2:
                task_id = cols[0]
                title = cols[1] if len(cols) > 1 else ""
                if re.match(r"T-\w+", task_id):
                    tasks.append(f"{task_id}: {title}")

    return tasks


def main() -> None:
    raw = sys.stdin.read().strip()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {}

    # Only fire on UserPromptSubmit
    if payload.get("hook_event_name", "") != "UserPromptSubmit":
        sys.exit(0)

    prompt = payload.get("prompt", "")
    if not START_PATTERNS.search(prompt):
        sys.exit(0)

    cwd = payload.get("cwd", os.getcwd())

    # ── Is this an OpenUP project? ────────────────────────────────────────────
    status_path = Path(cwd) / "docs" / "project-status.md"
    if not status_path.exists():
        sys.exit(0)

    fields = parse_project_status(status_path)
    status = fields.get("Status", "").lower()
    current_task = fields.get("Current Task", "None").strip()

    # No active iteration — nothing to warn about
    if status != "in-progress":
        sys.exit(0)

    # ── Gather evidence of unfinished work ────────────────────────────────────
    issues: list[str] = []
    suggestions: list[str] = []

    # 1. Active iteration in project-status
    task_label = current_task if current_task not in ("", "None", "none", "-") else "unknown"
    issues.append(f"  ⚠️  Active iteration — task {task_label} is marked in-progress")

    # 2. In-progress tasks in roadmap
    roadmap_path = Path(cwd) / "docs" / "roadmap.md"
    inprogress = find_inprogress_tasks(roadmap_path)
    if inprogress:
        task_list = "\n".join(f"      • {t}" for t in inprogress)
        issues.append(f"  ⚠️  Tasks still in-progress in docs/roadmap.md:\n{task_list}")

    # 3. Uncommitted changes
    _, dirty = run("git status --porcelain", cwd)
    if dirty:
        changed_files = dirty.splitlines()
        preview = "\n".join(f"      {l}" for l in changed_files[:5])
        extra = f"\n      ... and {len(changed_files) - 5} more" if len(changed_files) > 5 else ""
        issues.append(f"  ⚠️  Uncommitted changes:\n{preview}{extra}")
        suggestions.append("commit or stash your changes first")

    # 4. Unmerged commits on task branch
    _, branch = run("git rev-parse --abbrev-ref HEAD", cwd)
    trunk = get_trunk(cwd)
    if branch not in ("main", "master", trunk):
        _, unpushed = run(f"git log origin/{trunk}..HEAD --oneline 2>/dev/null || git log {trunk}..HEAD --oneline 2>/dev/null", cwd)
        if unpushed:
            commit_lines = unpushed.splitlines()
            preview = "\n".join(f"      {l}" for l in commit_lines[:5])
            extra = f"\n      ... and {len(commit_lines) - 5} more" if len(commit_lines) > 5 else ""
            issues.append(
                f"  ⚠️  Branch '{branch}' has {len(commit_lines)} unmerged commit(s):\n{preview}{extra}"
            )
            suggestions.append("create a PR or merge this branch before starting new work")

    if not issues:
        sys.exit(0)

    issues_text = "\n\n".join(issues)
    suggestions_text = (
        ("\n  Also: " + "; ".join(suggestions)) if suggestions else ""
    )

    print(
        f"[check-unfinished-tasks] ⚠️  Unfinished work detected — starting a new iteration is blocked.\n\n"
        f"Current state:\n\n{issues_text}\n\n"
        f"Recommended actions:\n\n"
        f"  1. Complete the current task:\n"
        f"       /openup-complete-task\n"
        f"     This will commit remaining work, create the PR, log the run,\n"
        f"     and update project-status.md to 'completed'.\n\n"
        f"  2. Or explicitly defer it (if you're pivoting to higher-priority work):\n"
        f"     Update docs/roadmap.md — change the task status to 'deferred',\n"
        f"     then update docs/project-status.md Status to 'deferred'.\n"
        f"     Then re-run the start-iteration command.{suggestions_text}",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
