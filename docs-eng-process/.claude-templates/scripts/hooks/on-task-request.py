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
the hook tells Claude to run /openup-start-iteration first, then work the
task sequentially (one agent, assuming roles as needed).

If an iteration IS already in-progress, the hook reminds Claude to continue
the work from the repo state. Teams are opt-in (full / multi-role work or
explicit request), not the default — solo sequential work is expected.

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

# Skip if this is already an OpenUP skill invocation. ANY /openup-* skill has
# its own flow (start-iteration, next, create-task-spec, create-vision, explore,
# …) and must not be bounced back to start-iteration — otherwise authoring the
# very spec a task needs ("/openup-create-task-spec task_id: T-002") gets blocked
# because no iteration exists, while no iteration can start without the spec.
OPENUP_SKILL_RE = re.compile(r"/openup-[a-z][a-z-]*", re.IGNORECASE)

# Track-suggestion heuristics (T-010). Keep these small and pure so the
# classifier can be unit-tested directly. quick wins over full when both match
# (a small-scoped word is a stronger signal than a broad-refactor word); full
# wins over standard. standard is the default fallthrough.
QUICK_TRACK_RE = re.compile(
    r"\b("
    r"typo|rename|comment|bump|version|docs?|readme|"
    r"format(?:ting)?|lint|whitespace|small|tiny|one[- ]?liner"
    r")\b",
    re.IGNORECASE,
)
FULL_TRACK_RE = re.compile(
    r"\b("
    r"architectural|architecture|redesign|across|migrate|migration|"
    r"multi[- ]?(?:role|component|service)|rework|schema\s+change|"
    r"broad\s+refactor"
    r")\b",
    re.IGNORECASE,
)


# Spine artifacts (vision, risk-list, use-case, architecture notebook, test
# plan) are substantive even when a quick signal like "docs"/"readme" also
# matches — they carry the plan gate and a rubric. Keep them off the quick track
# regardless: standard, or full when a broad-scope signal is also present.
SPINE_RE = re.compile(
    r"\b("
    r"vision|risk[- ]?list|use[- ]?case|"
    r"architecture(?:\s+notebook)?|test[- ]?plan"
    r")\b",
    re.IGNORECASE,
)


def suggest_track(prompt: str) -> str:
    """Classify a task-request prompt into a suggested ceremony track.

    Returns one of ``"quick"``, ``"full"``, ``"standard"``. Spine artifacts are
    forced off quick (standard, or full if a broad signal is present). Otherwise
    quick takes precedence over full (a small-scope signal is decisive); full
    takes precedence over the standard default. Pure and side-effect free.
    """
    if SPINE_RE.search(prompt):
        return "full" if FULL_TRACK_RE.search(prompt) else "standard"
    if QUICK_TRACK_RE.search(prompt):
        return "quick"
    if FULL_TRACK_RE.search(prompt):
        return "full"
    return "standard"


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
    track = suggest_track(prompt)

    if status != "in-progress":
        # No active iteration — must start one
        task_arg = f"task_id: {task_id}" if task_id else "task_id: T-XXX"
        print(
            f"[on-task-request] 🚦 Task request detected — start an OpenUP iteration first.\n\n"
            f"Do NOT explore files, read code, or write anything yet. First:\n\n"
            f"  1. Run: /openup-start-iteration {task_arg} track: {track}\n\n"
            f"  2. Read the change spec (docs/changes/<task>/plan.md) and work it\n"
            f"     yourself, sequentially — assume roles as needed (analyst →\n"
            f"     developer → tester). Persist progress to the repo between steps.\n\n"
            f"Teams are OPT-IN, not the default. Deploy {suggested_team} only for\n"
            f"full / multi-role work, or pass team: / deploy_team: true when you want\n"
            f"parallel specialists or independent review. A single-lane task needs no team.\n\n"
            f"Suggested track: {track} — adjust if the scope differs (see tracks.md).\n"
            f"Project phase: {phase} | No active iteration",
            file=sys.stderr,
        )
        sys.exit(0)  # advisory only — never block the user's prompt

    else:
        # Iteration is active — remind Claude to continue from repo state, solo by default
        active_task = current_task if current_task not in ("", "None", "none") else task_id or "?"
        print(
            f"[on-task-request] 🚦 Active iteration detected (task {active_task}).\n\n"
            f"Continue the work yourself, sequentially:\n\n"
            f"  1. Read the change folder (docs/changes/{active_task}/) for where it stands.\n\n"
            f"  2. Do the next step, assuming roles as needed (analyst → developer → tester).\n\n"
            f"  3. Persist progress to the repo (spec / design.md / run log) before stopping.\n\n"
            f"Working solo on a single-lane task is the default and expected. A team is\n"
            f"opt-in — deploy {suggested_team} only for full / multi-role work or to get\n"
            f"independent review.\n\n"
            f"Suggested track: {track} — adjust if the scope differs (see tracks.md).",
            file=sys.stderr,
        )
        sys.exit(0)  # advisory only — never block the user's prompt


if __name__ == "__main__":
    main()
