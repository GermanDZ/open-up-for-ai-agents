#!/usr/bin/env python3
"""
check-iteration.py — OpenUP hook: fires before every Bash tool call.

Intercepts `git commit` commands and verifies the agent is working inside
an active OpenUP iteration. Emits a strong warning if not, but does NOT
block — the commit proceeds. This allows legitimate completion-flow commits
(e.g. docs committed after project-status is set to 'completed') without
requiring a workaround.

An "active iteration" is indicated by ALL of:
  1. docs/project-status.md exists (project is OpenUP-managed)
  2. **Status** field is "in-progress"
  3. **Current Task** is not "None" / empty
  4. Current git branch is NOT trunk (main/master)

Bypass:
  Include [openup-skip] anywhere in the commit message to suppress the
  warning entirely. Bypasses are logged to .claude/memory/bypass-log.md
  so they can be audited.

  Example:
    git commit -m "chore: one-off cleanup [openup-skip]"

Exit codes:
  0 — always (warning only, never blocks)

Hook event: PreToolUse / Bash
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

COMMIT_RE = re.compile(r"\bgit\b.*\bcommit\b", re.DOTALL)
MSG_FLAG_RE = re.compile(r"(?:-m|--message)\s", re.DOTALL)
MSG_RE = re.compile(
    r"""(?:-m|--message)\s+(?:'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)")""",
    re.DOTALL,
)
SKIP_RE = re.compile(r"\[openup-skip\]", re.IGNORECASE)


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
        for line in path.read_text().splitlines():
            m = re.match(r"\*\*(.+?)\*\*:\s*(.*)", line)
            if m:
                fields[m.group(1).strip()] = m.group(2).strip()
    except OSError:
        pass
    return fields


def extract_message(command: str) -> str | None:
    m = MSG_RE.search(command)
    if not m:
        return None
    msg = (m.group(1) or m.group(2) or "").strip()
    return None if msg.startswith("$(") else msg


def log_bypass(cwd: str, branch: str, msg: str) -> None:
    """Append a bypass record to .claude/memory/bypass-log.md."""
    log_path = Path(cwd) / ".claude" / "memory" / "bypass-log.md"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        entry = f"- `{ts}` | branch: `{branch}` | message: `{msg[:80]}`\n"
        with log_path.open("a") as f:
            if log_path.stat().st_size == 0:
                f.write("# OpenUP Iteration-Check Bypasses\n\n"
                        "Commits that used `[openup-skip]` to suppress the iteration check.\n"
                        "Review periodically — frequent bypasses indicate a process gap.\n\n")
            f.write(entry)
    except OSError:
        pass  # Don't fail the hook if logging fails


def main() -> None:
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

    if "--amend" in command and not MSG_FLAG_RE.search(command):
        sys.exit(0)

    if "--allow-empty-message" in command:
        sys.exit(0)

    cwd = payload.get("cwd", os.getcwd())

    status_path = Path(cwd) / "docs" / "project-status.md"
    if not status_path.exists():
        sys.exit(0)

    # ── Check for explicit bypass ─────────────────────────────────────────────
    msg = extract_message(command)
    if msg and SKIP_RE.search(msg):
        _, branch = run("git rev-parse --abbrev-ref HEAD", cwd)
        log_bypass(cwd, branch, msg)
        print(
            f"[check-iteration] ⚠️  [openup-skip] detected — iteration check suppressed.\n"
            f"  Bypass logged to .claude/memory/bypass-log.md",
            file=sys.stderr,
        )
        sys.exit(0)

    # ── Parse project status ──────────────────────────────────────────────────
    fields = parse_project_status(status_path)
    status = fields.get("Status", "").lower()
    current_task = fields.get("Current Task", "None").strip()

    _, branch = run("git rev-parse --abbrev-ref HEAD", cwd)
    trunk = get_trunk(cwd)
    on_trunk = branch in ("main", "master", trunk)

    status_ok = status == "in-progress"
    task_ok = current_task not in ("", "None", "none", "-")
    branch_ok = not on_trunk

    if status_ok and task_ok and branch_ok:
        sys.exit(0)  # All clear

    # ── Build warning (no longer blocking) ───────────────────────────────────
    issues: list[str] = []
    if on_trunk:
        issues.append(f"  ⚠️  On trunk branch '{branch}' — work should happen on a task branch")
    if not status_ok:
        label = status if status else "unknown"
        issues.append(f"  ⚠️  Project status is '{label}' (expected 'in-progress')")
    if not task_ok:
        issues.append(f"  ⚠️  No current task assigned (Current Task: {current_task})")

    issues_text = "\n".join(issues)

    print(
        f"[check-iteration] ⚠️  No active OpenUP iteration — proceeding anyway.\n\n"
        f"Issues found:\n{issues_text}\n\n"
        f"If this is unintentional, initialize an iteration first:\n"
        f"  /openup-start-iteration task_id: T-XXX   (full task)\n"
        f"  /openup-quick-task task: \"description\"   (small change)\n\n"
        f"To suppress this warning for a one-off commit, add [openup-skip] to the message:\n"
        f"  git commit -m \"chore: description [openup-skip]\"\n"
        f"  Bypasses are logged to .claude/memory/bypass-log.md for auditing.",
        file=sys.stderr,
    )
    sys.exit(0)  # Warn but do not block


if __name__ == "__main__":
    main()
