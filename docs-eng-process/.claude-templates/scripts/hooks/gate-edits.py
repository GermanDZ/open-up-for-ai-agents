#!/usr/bin/env python3
"""
gate-edits.py — OpenUP hook: fires before every Edit / Write / NotebookEdit.

Gates edits to product/source code on an active OpenUP iteration with a
persisted plan. Process-state paths (explorations, .openup, memory, agent-logs)
are always exempt so the harness can manage its own bookkeeping.

Decision logic:
  1. Resolve the edit target path from tool_input
     (Edit/Write: file_path; NotebookEdit: notebook_path).
  2. If the target is an EXEMPT path → allow (exit 0).
  3. Otherwise the target is product/source code:
       - If .openup/state.json is absent → block (exit 2) with redirect.
       - If state exists but track == "quick" → allow (quick track needs
         state, not a plan); audit the bypass.
       - If state exists and gates.plan_persisted is false → block (exit 2).
       - Else (plan_persisted is a path) → allow.

Exit codes:
  0 — allow the edit
  2 — block; Claude sees the redirect guidance on stderr

Fail-open: any internal error allows the edit (a buggy gate must never brick
the user's editing session).

Hook event: PreToolUse / Edit|Write|NotebookEdit
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

EDIT_TOOLS = {"Edit", "Write", "NotebookEdit"}

# Paths that are process state / session debris, never product source.
# A target is exempt if any of these path segments appears in its
# repo-relative path.
EXEMPT_PREFIXES = (
    "docs/explorations/",
    ".openup/",
    ".claude/memory/",
    "docs/agent-logs/",
    "docs/iteration-retrospectives/",
)


def run(cmd: str, cwd: str) -> tuple[int, str]:
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True
    )
    return result.returncode, result.stdout.strip()


def state_get(cwd: str, key: str) -> tuple[int, str]:
    """Read a dotted key from .openup/state.json via openup-state.py.

    Returns (exit_code, stdout). Exit 3 = no state, 5 = key missing.
    """
    script = Path(cwd) / "scripts" / "openup-state.py"
    return run(
        f'python3 "{script}" get {key}',
        cwd,
    )


def rel_path(cwd: str, target: str) -> str:
    """Return the repo-relative, forward-slash path for the target."""
    p = Path(target)
    if not p.is_absolute():
        p = Path(cwd) / p
    try:
        rel = os.path.relpath(str(p), cwd)
    except ValueError:
        rel = target
    return rel.replace(os.sep, "/")


def is_exempt(rel: str) -> bool:
    # Normalize a leading "./" only (not arbitrary leading dots/slashes —
    # that would corrupt dot-prefixed dirs like ".openup/").
    norm = rel[2:] if rel.startswith("./") else rel
    return any(norm == pre.rstrip("/") or norm.startswith(pre)
               for pre in EXEMPT_PREFIXES)


def log_bypass(cwd: str, branch: str, msg: str) -> None:
    """Append a bypass record to .claude/memory/bypass-log.md."""
    log_path = Path(cwd) / ".claude" / "memory" / "bypass-log.md"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        entry = f"- `{ts}` | branch: `{branch}` | gate-edits | {msg[:120]}\n"
        with log_path.open("a") as f:
            if log_path.stat().st_size == 0:
                f.write("# OpenUP Iteration-Check Bypasses\n\n"
                        "Commits/edits that bypassed an OpenUP gate.\n"
                        "Review periodically — frequent bypasses indicate a process gap.\n\n")
            f.write(entry)
    except OSError:
        pass  # Don't fail the hook if logging fails


REDIRECT = (
    "[gate-edits] ❌ Editing source code with no active OpenUP iteration plan.\n\n"
    "A plan must be persisted before product/source code can be edited.\n\n"
    "Start an iteration first:\n"
    "  /openup-start-iteration task_id: T-XXX   (full task)\n"
    "  /openup-quick-task task: \"description\"   (small change)\n\n"
    "Process-state files (docs/explorations/, .openup/, .claude/memory/,\n"
    "docs/agent-logs/) are exempt and can be edited freely.\n\n"
    "If this edit is a deliberate one-off, run the appropriate skill rather\n"
    "than bypassing the gate."
)


def main() -> None:
    try:
        raw = sys.stdin.read().strip()
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {}

        tool_name = payload.get("tool_name", "")
        if tool_name not in EDIT_TOOLS:
            sys.exit(0)

        cwd = payload.get("cwd", os.getcwd())
        tool_input = payload.get("tool_input", {}) or {}

        # Resolve edit target.
        target = (
            tool_input.get("file_path")
            or tool_input.get("notebook_path")
            or ""
        )
        if not target:
            sys.exit(0)  # nothing to gate

        rel = rel_path(cwd, target)

        # Exempt process-state paths.
        if is_exempt(rel):
            sys.exit(0)

        # Target is product/source code. Read state.
        code, plan_out = state_get(cwd, "gates.plan_persisted")

        if code == 3:
            # No state file at all → block.
            print(REDIRECT, file=sys.stderr)
            sys.exit(2)

        if code != 0:
            # Any other state-read failure (e.g. key missing, invalid) → fail open.
            sys.exit(0)

        # State exists. Check track for the quick-track relaxation.
        tcode, track = state_get(cwd, "track")
        track = track.strip() if tcode == 0 else ""

        plan_val = plan_out.strip()
        plan_done = plan_val not in ("", "false", "null")

        if plan_done:
            sys.exit(0)  # plan persisted → allow

        if track == "quick":
            # Quick track requires state, not a plan → allow, but audit.
            _, branch = run("git rev-parse --abbrev-ref HEAD", cwd)
            log_bypass(cwd, branch, f"quick-track edit to {rel} (no plan gate)")
            sys.exit(0)

        # State present, not quick, plan not persisted → block.
        print(REDIRECT, file=sys.stderr)
        sys.exit(2)

    except SystemExit:
        raise
    except Exception:
        # Fail open: never brick the user's editing session.
        sys.exit(0)


if __name__ == "__main__":
    main()
