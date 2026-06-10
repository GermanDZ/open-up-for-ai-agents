#!/usr/bin/env python3
"""
on-stop.py — OpenUP hook: fires when the agent tries to stop.

Two layers of enforcement:

  1. Uncommitted-work block (existing): if the worktree is dirty, block stop
     so changes are not abandoned. EXEMPTION: docs/agent-logs/agent-runs.jsonl
     is hook-managed traceability appended by auto-log-commit AFTER each commit,
     so it always lags HEAD by one append and can never be committed in the
     commit it records. It is excluded from the dirty check (otherwise every
     commit re-dirties it and on-stop tail-chases forever); it stays tracked
     and is swept into the next code commit naturally. Only NON-exempt dirty
     files block stop.
  2. Unmet-gate block (new): if an OpenUP iteration is active (.openup/state.json
     present) and commits were made on this branch since trunk, then:
       - gates.log_written false → block (exit 2) naming the gate; or
       - gates.roadmap_synced false → block (exit 2) naming the gate.
     This gives Stop teeth: a session cannot end with commits but no log /
     no roadmap sync.

Exit codes:
  0 — all clear, stop proceeds
  2 — work/gate incomplete; Claude continues and sees the message on stderr

Fail-open on state-read failures: a broken state file must not trap the
session forever.

Hook event: Stop
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


# Hook-managed files that lag HEAD by design and must not block stop.
EXEMPT_DIRTY_PATHS = {"docs/agent-logs/agent-runs.jsonl"}


def run(cmd: str, cwd: str) -> tuple[int, str]:
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True
    )
    return result.returncode, result.stdout.strip()


def porcelain_path(line: str) -> str:
    """Extract the repo-relative path from a `git status --porcelain` line.

    Porcelain v1 format: `XY <path>` (status code in cols 0-1, space, path
    from col 3). Paths with special chars are double-quoted; renames/copies
    use `orig -> new` — we take the destination. Returns a forward-slash,
    unquoted path.
    """
    # Status is XY in cols 0-1 then a space; path begins at col 3. But callers
    # may pass a left-stripped line (e.g. run() strips the whole output, so a
    # leading-space status like " M path" loses its first column). Handle both
    # by stripping the leading status code + whitespace defensively rather than
    # slicing a fixed offset.
    m = re.match(r"^[ MADRCU?!]{1,2}\s+(.*)$", line)
    path = m.group(1) if m else line.strip()
    # Rename/copy: "orig -> new" → keep the destination.
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    path = path.strip()
    # Git quotes paths containing unusual chars; strip the surrounding quotes.
    if len(path) >= 2 and path.startswith('"') and path.endswith('"'):
        path = path[1:-1]
    return path


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


def state_get(cwd: str, key: str) -> tuple[int, str]:
    script = Path(cwd) / "scripts" / "openup-state.py"
    return run(f'python3 "{script}" get {key}', cwd)


def main() -> None:
    raw = sys.stdin.read().strip()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {}

    cwd = payload.get("cwd", os.getcwd())

    # 1. Check for uncommitted changes ────────────────────────────────────────
    #    The auto-log-commit hook (PostToolUse) appends to the tracked run log
    #    AFTER each commit, so docs/agent-logs/agent-runs.jsonl always lags HEAD
    #    by one append and can never be committed in the commit it records. That
    #    is hook-managed traceability, not abandoned work — it gets swept into
    #    the next code commit naturally. Exempt it here so it does not trap the
    #    session in an infinite tail-chase. The log stays TRACKED (the audit
    #    trail the 4-week re-audit depends on); it is just not a stop-blocker.
    _, dirty = run("git status --porcelain", cwd)
    if dirty:
        non_exempt = [
            line for line in dirty.splitlines()
            if porcelain_path(line) not in EXEMPT_DIRTY_PATHS
        ]
        if non_exempt:
            file_list = "\n".join(f"  {l}" for l in non_exempt[:10])
            extra = (
                f"\n  ... and {len(non_exempt) - 10} more"
                if len(non_exempt) > 10 else ""
            )
            print(
                f"[on-stop] ⚠️  UNCOMMITTED CHANGES — do not stop yet.\n\n"
                f"The following files have uncommitted changes:\n{file_list}{extra}\n\n"
                f"Please commit or stash these changes before stopping.\n"
                f"Use the canonical format: type(scope): description [T-XXX]",
                file=sys.stderr,
            )
            sys.exit(2)

    # 2. Unmet-gate block (only when an iteration is active) ──────────────────
    try:
        state_code, _ = state_get(cwd, "task_id")
        if state_code == 0:
            trunk = get_trunk(cwd)
            _, current_branch = run("git rev-parse --abbrev-ref HEAD", cwd)

            # Only enforce when commits exist on this branch beyond trunk.
            _, commits = run(
                f"git log origin/{trunk}..HEAD --oneline 2>/dev/null", cwd
            )
            if not commits:
                # Fall back to local trunk comparison if no remote tracking.
                _, commits = run(
                    f"git log {trunk}..HEAD --oneline 2>/dev/null", cwd
                )

            if commits:
                # Gate-read semantics (defense-in-depth):
                #   exit 0 → key present: truthy clears the block, "false" blocks.
                #   exit 5 → key MISSING on existing state: treat as UNMET → block
                #            (a malformed state must not silently skip enforcement).
                #   exit 3 → no state file at all: handled by the outer guard
                #            (state_code != 0), so we never reach here without state.
                #   any other code: fail open (handled by the except below).
                lcode, log_written = state_get(cwd, "gates.log_written")
                log_truthy = lcode == 0 and log_written.strip() not in ("false", "null", "")
                if lcode in (0, 5) and not log_truthy:
                    print(
                        f"[on-stop] ❌ Commits made but gates.log_written is not satisfied.\n\n"
                        f"Commits on {current_branch} since {trunk}:\n"
                        + "\n".join(f"  {l}" for l in commits.splitlines()[:10])
                        + "\n\nThe run log has not been written (gate false or absent).\n"
                        f"The auto-log-commit hook normally sets this on commit; if it\n"
                        f"is still unsatisfied, run /openup-log-run (or re-commit)\n"
                        f"before stopping.",
                        file=sys.stderr,
                    )
                    sys.exit(2)

                rcode, roadmap_synced = state_get(cwd, "gates.roadmap_synced")
                roadmap_truthy = (
                    rcode == 0 and roadmap_synced.strip() not in ("false", "null", "")
                )
                # Roadmap-sync is required once the run is logged: at that point the
                # iteration has progressed far enough that the roadmap must be in
                # sync. Block when roadmap_synced is unsatisfied — false OR absent
                # (exit 5) on existing state — given the log gate is satisfied.
                if log_truthy and rcode in (0, 5) and not roadmap_truthy:
                    print(
                        f"[on-stop] ❌ gates.roadmap_synced is false.\n\n"
                        f"The run was logged but the roadmap / project-status are not\n"
                        f"in sync with state. Run scripts/sync-status.py (or\n"
                        f"/openup-complete-task) before stopping so the roadmap and\n"
                        f"project-status.md cannot disagree.",
                        file=sys.stderr,
                    )
                    sys.exit(2)
    except Exception:
        # Fail open on any state-read failure — never trap the session.
        pass

    # 3. On trunk with unpushed commits — warn only ───────────────────────────
    trunk = get_trunk(cwd)
    _, current_branch = run("git rev-parse --abbrev-ref HEAD", cwd)
    if current_branch in ("main", "master", trunk):
        _, unpushed = run(f"git log origin/{trunk}..HEAD --oneline 2>/dev/null", cwd)
        if unpushed:
            print(
                f"[on-stop] ⚠️  On trunk ({current_branch}) with unpushed commits.\n"
                f"Consider pushing or creating a PR before ending the session:\n"
                + "\n".join(f"  {l}" for l in unpushed.splitlines()),
                file=sys.stderr,
            )
            sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
