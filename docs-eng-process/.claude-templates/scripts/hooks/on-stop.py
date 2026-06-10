#!/usr/bin/env python3
"""
on-stop.py — OpenUP hook: fires when the agent tries to stop.

Two layers of enforcement:

  1. Uncommitted-work block (existing): if the worktree is dirty, block stop
     so changes are not abandoned.
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
import subprocess
import sys
from pathlib import Path


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
    _, dirty = run("git status --porcelain", cwd)
    if dirty:
        lines = dirty.splitlines()
        file_list = "\n".join(f"  {l}" for l in lines[:10])
        extra = f"\n  ... and {len(lines) - 10} more" if len(lines) > 10 else ""
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
