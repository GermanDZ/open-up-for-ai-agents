#!/usr/bin/env python3
"""
on-task-request.py — OpenUP hook: fires on UserPromptSubmit.

Detects when the user submits a task request in an OpenUP project and
injects a PM-intake instruction BEFORE Claude does any exploration or
implementation work.

A "task request" is any message that:
  - References a task ID (T-001, T-010b, T-12, etc.)
  - OR contains task-start language ("continue with", "work on", "implement",
    "start", "fix", "build", "add", "create feature", etc.)

If the project is OpenUP-managed and no iteration is currently in-progress,
the hook tells Claude to act as PM and run /openup-start-iteration first.

If an iteration IS already in-progress, the hook reminds Claude to act as
PM and coordinate the team rather than working solo.

Exit codes:
  0 — not an OpenUP project, OR not a task request
  2 — task request detected — inject PM-intake instruction via stderr

Hook event: UserPromptSubmit
"""

import json
import os
import re
import sys
from pathlib import Path

# Task ID pattern: T-001, T-010b, T-12, t-7, etc.
TASK_ID_RE = re.compile(r"\bT-\d+[a-z]?\b", re.IGNORECASE)

# Task-start language patterns
TASK_LANG_RE = re.compile(
    r"\b("
    r"continue\s+with|work\s+on|start\s+(?:task|working|implementing|on)|"
    r"implement|let'?s\s+(?:work|start|implement|build|fix)|"
    r"pick\s+up|resume|proceed\s+with|"
    r"build\s+(the|a|this)|fix\s+(?:the|a|this)|"
    r"add\s+(the|a|this)\s+(?:feature|functionality)|"
    r"develop|complete\s+(?:the|task)"
    r")\b",
    re.IGNORECASE,
)

# Skip if this is already an OpenUP skill invocation (handled by other hooks)
OPENUP_SKILL_RE = re.compile(
    r"/openup-(?:start-iteration|complete-task|quick-task|orchestrate|"
    r"inception|elaboration|construction|transition|phase-review)",
    re.IGNORECASE,
)


def parse_project_status(path: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    try:
        for line in path.read_text().splitlines():
            m = re.match(r"\*\*(.+?)\*\*:\s*(.*)", line)
            if m:
                fields[m.group(1).strip()] = m.group(2).strip()
    except OSError:
        pass
    return fields


def main() -> None:
    raw = sys.stdin.read().strip()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {}

    if payload.get("hook_event_name", "") != "UserPromptSubmit":
        sys.exit(0)

    prompt = payload.get("prompt", "")

    # Skip if already using an OpenUP skill — those have their own flow
    if OPENUP_SKILL_RE.search(prompt):
        sys.exit(0)

    # Is this a task request?
    task_id_match = TASK_ID_RE.search(prompt)
    has_task_lang = bool(TASK_LANG_RE.search(prompt))

    if not task_id_match and not has_task_lang:
        sys.exit(0)

    cwd = payload.get("cwd", os.getcwd())

    # Only act on OpenUP-managed projects
    status_path = Path(cwd) / "docs" / "project-status.md"
    if not status_path.exists():
        sys.exit(0)

    # Read current project state
    fields = parse_project_status(status_path)
    status = fields.get("Status", "").lower()
    current_task = fields.get("Current Task", "None").strip()
    phase = fields.get("Phase", "construction").strip().lower()

    task_id = task_id_match.group(0).upper() if task_id_match else None

    phase_team_map = {
        "inception": "openup-inception-team (analyst + project-manager)",
        "elaboration": "openup-elaboration-team (architect + developer)",
        "construction": "openup-construction-team (developer + tester)",
        "transition": "openup-transition-team (developer + tester + project-manager)",
    }
    suggested_team = phase_team_map.get(phase, "openup-construction-team (developer + tester)")

    if status != "in-progress":
        # No active iteration — must start one
        task_arg = f" task_id: {task_id}" if task_id else " task_id: T-XXX"
        print(
            f"[on-task-request] 🚦 Task request detected — OpenUP PM intake required.\n\n"
            f"You are the Project Manager. Do NOT explore files, read code, or write\n"
            f"anything yet. Follow this sequence:\n\n"
            f"  1. Run: /openup-start-iteration{task_arg}\n"
            f"     This will deploy the {suggested_team}.\n\n"
            f"  2. As PM, decompose the task goal into role-specific subtasks.\n\n"
            f"  3. Brief each specialist (developer, tester, architect as needed)\n"
            f"     using the delegation format from your Orchestrator Protocol.\n\n"
            f"  4. Collect outputs and synthesize.\n\n"
            f"Project phase: {phase} | No active iteration\n"
            f"Start the iteration first — then coordinate the team.",
            file=sys.stderr,
        )
        sys.exit(2)

    else:
        # Iteration is active — remind Claude to act as PM, not solo
        active_task = current_task if current_task not in ("", "None", "none") else task_id or "?"
        print(
            f"[on-task-request] 🚦 Active iteration detected (task {active_task}).\n\n"
            f"You are the Project Manager. Do not work solo. Coordinate the team:\n\n"
            f"  1. Confirm the team is deployed (if not, spawn {suggested_team} now).\n\n"
            f"  2. Decompose the work into specialist subtasks.\n\n"
            f"  3. Brief each specialist and collect their outputs.\n\n"
            f"  4. Synthesize and verify against acceptance criteria.\n\n"
            f"If the team is already active, send them their next subtask.\n"
            f"Do not write code or modify files directly — delegate to specialists.",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
