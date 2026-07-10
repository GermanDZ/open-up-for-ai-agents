#!/usr/bin/env python3
"""
validate-commit.py — OpenUP hook: fires before every Bash tool call.

Intercepts `git commit` commands and validates that the commit message
follows the canonical OpenUP format:

  type(scope): description [T-XXX]

Where:
  type   = feat | fix | refactor | test | docs | chore | style | perf | ci
  scope  = affected module/area (optional but encouraged)
  T-XXX  = task ID from roadmap

  The [T-XXX] tag is OPTIONAL by default, but becomes MANDATORY when an
  OpenUP iteration is active (.openup/state.json present with a task_id):
  in that case a subject without a matching tag is rejected (exit 2) and the
  error suggests the state's task_id.

Bypass:
  Include [openup-skip] anywhere in the commit message to suppress all
  validation. Bypasses are logged to .claude/memory/bypass-log.md.

Exit codes:
  0 — not a git commit, OR commit message is valid — allow the command
  2 — commit message is malformed (or missing required [T-XXX]) — block

Hook event: PreToolUse / Bash
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

VALID_TYPES = {
    "feat", "fix", "refactor", "test", "docs", "chore",
    "style", "perf", "ci", "build", "revert", "quick",
}

# Canonical format: type(scope): description  (task id checked separately)
PATTERN = re.compile(
    r"^("
    + "|".join(VALID_TYPES)
    + r")(\([^)]+\))?!?: .{3,}"
)

# Patterns that indicate this bash command is a git commit
COMMIT_RE = re.compile(r'\bgit\b.*\bcommit\b', re.DOTALL)

# Extract -m / --message value (handles single and double quotes)
MSG_RE = re.compile(
    r"""(?:-m|--message)\s+(?:'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)")""",
    re.DOTALL,
)

SKIP_RE = re.compile(r"\[openup-skip\]", re.IGNORECASE)

# A task tag like [T-006]
TASK_TAG_RE = re.compile(r"\[T-\d+\]", re.IGNORECASE)


def run(cmd: str, cwd: str) -> tuple[int, str]:
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True
    )
    return result.returncode, result.stdout.strip()


def state_task_id(cwd: str) -> str | None:
    """Return state.json task_id, or None if no state / read failure."""
    try:
        script = Path(cwd) / "scripts" / "openup-state.py"
        code, out = run(f'python3 "{script}" get task_id', cwd)
        if code == 0:
            tid = out.strip()
            return tid or None
    except Exception:
        return None
    return None


def log_bypass(cwd: str, branch: str, msg: str) -> None:
    log_path = Path(cwd) / ".claude" / "memory" / "bypass-log.md"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        entry = f"- `{ts}` | branch: `{branch}` | validate-commit | message: `{msg[:80]}`\n"
        with log_path.open("a") as f:
            if log_path.stat().st_size == 0:
                f.write("# OpenUP Iteration-Check Bypasses\n\n"
                        "Commits/edits that bypassed an OpenUP gate.\n"
                        "Review periodically — frequent bypasses indicate a process gap.\n\n")
            f.write(entry)
    except OSError:
        pass


def extract_commit_message(command: str) -> str | None:
    """Return the commit message string, or None if we can't extract it."""
    m = MSG_RE.search(command)
    if not m:
        return None
    msg = (m.group(1) or m.group(2) or "").strip()
    if msg.startswith("$("):
        return None
    return msg


def first_line(msg: str) -> str:
    return msg.split("\n")[0].strip()


def main() -> None:
    raw = sys.stdin.read().strip()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {}

    tool_name = payload.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command = payload.get("tool_input", {}).get("command", "")

    # Only act on git commit commands
    if not COMMIT_RE.search(command):
        sys.exit(0)

    # Skip --amend without -m (uses existing message)
    if "--amend" in command and not re.search(r"(?:-m|--message)\s", command):
        sys.exit(0)

    # Skip --allow-empty-message
    if "--allow-empty-message" in command:
        sys.exit(0)

    msg = extract_commit_message(command)
    if msg is None:
        # Can't extract message (e.g. uses heredoc or -F flag) — allow through
        sys.exit(0)

    cwd = payload.get("cwd", os.getcwd())

    # [openup-skip] bypass — audit and allow.
    if SKIP_RE.search(msg):
        _, branch = run("git rev-parse --abbrev-ref HEAD", cwd)
        log_bypass(cwd, branch, msg)
        print(
            "[validate-commit] ⚠️  [openup-skip] detected — commit validation "
            "suppressed.\n  Bypass logged to .claude/memory/bypass-log.md",
            file=sys.stderr,
        )
        sys.exit(0)

    subject = first_line(msg)

    # Check for "Co-Authored-By" trailer only — those are fine
    if subject.startswith("Co-Authored-By"):
        sys.exit(0)

    # Format check (type(scope): description).
    if not PATTERN.match(subject):
        print(
            f"[validate-commit] ❌ Commit message does not follow the canonical format.\n\n"
            f"  Your message:    {subject!r}\n\n"
            f"  Required format: type(scope): description [T-XXX]\n"
            f"  Valid types:     {', '.join(sorted(VALID_TYPES))}\n\n"
            f"  Examples:\n"
            f"    feat(auth): add JWT token validation [T-007]\n"
            f"    fix(api): handle null upstream response\n"
            f"    docs: update architecture notebook\n"
            f"    refactor(cache): simplify TTL calculation [T-012]\n\n"
            f"Please rewrite the commit message to match the format, then retry.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Mandatory-tag check: if an iteration is active with a task_id, the
    # subject MUST carry the lane's own [task_id] tag — OR any [T-XXX] tag as an
    # alternative (so a commit that references a related numeric task id still
    # passes). The lane tag is matched literally (regex-escaped) so a non-numeric
    # id like a quick-task slug is accepted; this keeps the error message's own
    # suggestion ("Append [task_id]") satisfiable for any active id (T-070).
    task_id = state_task_id(cwd)
    lane_tag_re = re.compile(r"\[" + re.escape(task_id) + r"\]", re.IGNORECASE) if task_id else None
    has_tag = bool(TASK_TAG_RE.search(subject)) or bool(lane_tag_re and lane_tag_re.search(subject))
    if task_id and not has_tag:
        print(
            f"[validate-commit] ❌ Missing required task tag.\n\n"
            f"  Your message:    {subject!r}\n\n"
            f"  An OpenUP iteration is active for task {task_id}, so the commit\n"
            f"  subject must carry the task tag. Append [{task_id}]:\n\n"
            f"    {subject} [{task_id}]\n\n"
            f"  (Use [openup-skip] to bypass for a deliberate one-off; bypasses\n"
            f"  are audited in .claude/memory/bypass-log.md.)",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
