#!/usr/bin/env python3
"""
gate-edits.py — OpenUP hook: fires before every Edit / Write / NotebookEdit.

Gates edits to product/source code on an active OpenUP iteration with a
persisted plan. Process-state paths (explorations, .openup, memory, agent-logs,
change folders docs/changes/, plan-mode plans) are always exempt so the harness
can manage its own bookkeeping and author task specs before an iteration exists.

State is resolved from the worktree that OWNS the edited file, not the harness
cwd — so worktree-per-task edits read the task worktree's state.json instead of
false-blocking on the main repo's.

Decision logic:
  1. Resolve the edit target path from tool_input
     (Edit/Write: file_path; NotebookEdit: notebook_path).
  2. If the target is a plan-mode plan (…/.claude/plans/) → allow (exit 0).
  3. If the target is an EXEMPT path → allow (exit 0).
  4. Otherwise the target is product/source code (state read from its
     worktree root):
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
    # Fully-derived view: written only by sync-status.py and process skills
    # (start-iteration, retrospective) — never hand-authored source. Gating it
    # blocked /openup-retrospective's own step 7. The write-fence still governs
    # it on task branches via the fresh-base rule.
    "docs/project-status.md",
    # Ring 2 change-state: plan.md / design.md / inputs / test-notes. These ARE
    # the plan the gate wants persisted before code — gating their authoring is
    # a chicken-and-egg block that stops /openup-create-task-spec from writing
    # the spec on trunk pre-iteration. None are product source. The write-fence
    # (openup-fence.py) still confines a lane's diff to its own T-NNN/ folder.
    "docs/changes/",
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


# Plan-mode plan files (…/.claude/plans/<name>.md) are process state, like
# docs/explorations/ — they record intent before an iteration exists. The harness
# writes them under $HOME (outside any repo), so this is an absolute-path segment
# check rather than a repo-relative prefix.
PLAN_MODE_SEGMENT = "/.claude/plans/"


def abs_target(cwd: str, target: str) -> str:
    p = Path(target)
    if not p.is_absolute():
        p = Path(cwd) / p
    return str(p).replace(os.sep, "/")


def is_plan_mode_path(abs_t: str) -> bool:
    return PLAN_MODE_SEGMENT in abs_t


def resolve_state_root(cwd: str, target: str) -> str:
    """Repo/worktree root that owns the edited file.

    With worktree-per-task, ``.openup/state.json`` lives in the task worktree
    while the harness cwd stays pinned to the main repo. Reading state from cwd
    then false-blocks a legitimate edit *inside* the worktree. Resolve the root
    from the edit target instead (nearest existing ancestor → ``git
    rev-parse --show-toplevel``). Falls back to cwd when git can't resolve, in
    keeping with the hook's fail-open contract.
    """
    p = Path(target)
    if not p.is_absolute():
        p = Path(cwd) / p
    d = p.parent
    while not d.exists() and d != d.parent:
        d = d.parent
    if d.exists():
        code, out = run("git rev-parse --show-toplevel", str(d))
        if code == 0 and out:
            return out
    return cwd


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
    "docs/agent-logs/, docs/iteration-retrospectives/, docs/project-status.md,\n"
    "docs/changes/) and any path outside this repo are exempt and can be\n"
    "edited freely.\n\n"
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

        # Plan-mode plan files are process state (may live under $HOME).
        if is_plan_mode_path(abs_target(cwd, target)):
            sys.exit(0)

        # Resolve state from the worktree that owns the edit, not the harness
        # cwd (worktree-per-task puts state.json in the task worktree).
        state_root = resolve_state_root(cwd, target)
        rel = rel_path(state_root, target)

        # A target outside the repo/worktree root cannot be this project's
        # source — e.g. the harness memory dir ~/.claude/projects/<id>/memory/,
        # or a path on another drive (relpath raised, leaving an absolute rel).
        # Never gate it; the iteration only governs files inside the repo.
        if rel.startswith("../") or os.path.isabs(rel):
            sys.exit(0)

        # Exempt process-state paths.
        if is_exempt(rel):
            sys.exit(0)

        # Target is product/source code. Read state.
        code, plan_out = state_get(state_root, "gates.plan_persisted")

        if code == 3:
            # No state file at all → block.
            print(REDIRECT, file=sys.stderr)
            sys.exit(2)

        if code != 0:
            # Any other state-read failure (e.g. key missing, invalid) → fail open.
            sys.exit(0)

        # State exists. Check track for the quick-track relaxation.
        tcode, track = state_get(state_root, "track")
        track = track.strip() if tcode == 0 else ""

        plan_val = plan_out.strip()
        plan_done = plan_val not in ("", "false", "null")

        if plan_done:
            sys.exit(0)  # plan persisted → allow

        if track == "quick":
            # Quick track requires state, not a plan → allow, but audit.
            _, branch = run("git rev-parse --abbrev-ref HEAD", state_root)
            log_bypass(state_root, branch, f"quick-track edit to {rel} (no plan gate)")
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
