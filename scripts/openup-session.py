#!/usr/bin/env python3
"""OpenUP atomic session lifecycle — begin | end (T-063).

One process acquires (``begin``) or tears down (``end``) a lane's **claim + iteration
state + log** so the sequential ``/openup-next`` loop stops chaining six separate Bash
round-trips and, crucially, cannot leave a *half-acquired* session behind when a step
fails mid-way.

Design rules (do not break these — they are the task's safeguards):

  * **Composition-only.** This module owns **no** claim/state logic. It loads
    ``openup-claims.py`` and ``openup-state.py`` via importlib (their filenames are
    hyphenated) and drives them through their existing ``main(argv)`` entry points.
    If you find yourself re-implementing ``write_claim_atomic`` or a state dict here,
    stop — call the module instead.
  * **Git stays in the skills.** ``begin`` never creates a branch/worktree and ``end``
    never removes one. The skill creates the worktree first, then calls ``begin`` with
    its paths; ``/openup-complete-task`` removes the worktree after ``end``.
  * **Atomic begin.** The rollback boundary is *after the claim is written*: if any of
    heartbeat / state-init / log fails, the claim taken this call is released so no
    orphan lease remains (Requirement 2 / DD3).

See ``docs/changes/T-063/plan.md`` and ``design.md`` for the full contract.
"""

import argparse
import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Load the sibling modules (hyphenated filenames → importlib), never re-implement.
# --------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent


def _load(mod_name: str, filename: str):
    path = _HERE / filename
    spec = importlib.util.spec_from_file_location(mod_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


claims = _load("openup_claims", "openup-claims.py")
state = _load("openup_state", "openup-state.py")

# Default stale threshold for the begin-time dry-run reap warning. Mirrors
# openup-claims.py's `reap --stale-after` default (1800s = 30 min).
DEFAULT_STALE_AFTER = 1800


# --------------------------------------------------------------------------
# Composition helper — run a module's CLI in-process, normalizing exit signal.
# --------------------------------------------------------------------------
def _run(module, argv, echo=True):
    """Invoke ``module.main(argv)`` in-process and return (code, captured_stdout).

    ``main()`` returns the subcommand's exit code, but some cmd_* handlers raise
    ``SystemExit`` instead (cmd_init on an existing file, cmd_archive on invalid
    state, cmd_get on a missing key). Normalize both to an int so the caller can
    branch on failure.

    The composed subcommand's stdout is ALWAYS captured so that ``begin``/``end``
    can keep their own stdout as pure JSON (the skills parse it). By default the
    captured chatter (``Claimed …``, ``Initialized …``, ``logged …``) is echoed to
    stderr so it stays visible; pass ``echo=False`` to filter it yourself.
    """
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = module.main(argv)
    except SystemExit as exc:  # some handlers exit instead of returning
        code = exc.code
    if code is None:
        code = 0
    if not isinstance(code, int):  # SystemExit("message") → treat as failure
        code = 1
    if echo and buf.getvalue():
        sys.stderr.write(buf.getvalue())
    return code, buf.getvalue()


# --------------------------------------------------------------------------
# begin
# --------------------------------------------------------------------------
def cmd_begin(args):
    task = args.task_id
    claims_flags = []
    if args.claims_dir:
        claims_flags += ["--claims-dir", args.claims_dir]
    push_flags = ["--no-push"] if args.no_push else []

    # 1. Stale-lease reap — DEFAULT is dry-run + warn (does not change begin's
    #    blast radius; DD4). --reap opts into a live sweep. The live self-heal
    #    that the loop relies on lives in `openup-board.py refresh`, not here.
    reap_argv = ["reap", "--stale-after", str(args.stale_after)] + claims_flags
    if not args.reap:
        reap_argv.append("--dry-run")
    _, reap_out = _run(claims, reap_argv, echo=False)
    for line in reap_out.splitlines():
        # Surface only actionable lines (candidates / actual reaps), not the summary.
        if line.startswith("would reap ") or line.startswith("reaped "):
            sys.stderr.write(f"[session begin] {line}\n")

    # 2. Remote-check (T-044) — advisory, fail-open. Exit 9 = another clone owns
    #    this task; abort BEFORE claiming (nothing to roll back).
    # remote-check is advisory and takes no --claims-dir (it inspects git refs,
    # not the local claims dir).
    rc_argv = ["remote-check", "--task-id", task]
    if args.branch:
        rc_argv += ["--self-branch", args.branch]
    code, _ = _run(claims, rc_argv)
    if code == claims.EXIT_REMOTE_DUP:
        sys.stderr.write(
            f"REFUSED: {task} is already owned by another clone on the remote. "
            f"Do not proceed.\n"
        )
        return code

    # 3. Claim (runs preflight internally). No claim yet → failure needs no rollback.
    claim_argv = ["claim", "--task-id", task, "--session-id", args.session_id or task]
    if args.branch:
        claim_argv += ["--branch", args.branch]
    if args.worktree:
        claim_argv += ["--worktree", args.worktree]
    if args.touches:
        claim_argv += ["--touches", args.touches]
    if args.depends_on:
        claim_argv += ["--depends-on", args.depends_on]
    claim_argv += push_flags + claims_flags
    code, _ = _run(claims, claim_argv)
    if code != claims.EXIT_OK:
        sys.stderr.write(f"REFUSED: could not claim {task} (code {code}).\n")
        return code

    # --- Rollback boundary: the claim now exists. Any failure below releases it
    #     so no half-acquired session remains (Requirement 2). Only remove the
    #     state file when THIS call created it (remove_state=True, the log-failure
    #     branch); never delete a state.json that begin refused to overwrite — it
    #     belongs to another session.
    def _rollback(remove_state=False):
        if remove_state:
            try:
                sp = state.state_path(args)
                if sp.exists():
                    sp.unlink()
            except Exception:  # best-effort; releasing the claim is the essential part
                pass
        _run(claims, ["release", "--task-id", task, "--no-push"] + claims_flags)

    # 4. Heartbeat — opts the claim into the reaper model (T-060).
    code, _ = _run(claims, ["heartbeat", "--task-id", task] + claims_flags)
    if code != claims.EXIT_OK:
        _rollback()
        sys.stderr.write(f"begin failed at heartbeat (code {code}); claim rolled back.\n")
        return code or 1

    # 5. Iteration state init.
    init_argv = [
        "init", "--task-id", task,
        "--iteration", str(args.iteration),
        "--phase", args.phase,
        "--track", args.track,
    ]
    if args.branch:
        init_argv += ["--branch", args.branch]
    if args.worktree:
        init_argv += ["--worktree", args.worktree]
    if args.session_id:
        init_argv += ["--session-id", args.session_id]
    if args.plan:
        init_argv += ["--plan", args.plan]
    if args.iterations_since_retro is not None:
        init_argv += ["--iterations-since-retro", str(args.iterations_since_retro)]
    if args.force:
        init_argv.append("--force")
    if args.state_dir:
        init_argv += ["--state-dir", args.state_dir]
    code, _ = _run(state, init_argv)
    if code not in (0, None):
        _rollback()
        sys.stderr.write(f"begin failed at state-init (code {code}); claim rolled back.\n")
        return code or 1

    # 6. Log the session_begin event.
    log_argv = ["log-event", "--event", "session_begin", "--task-id", task]
    if args.goal:
        log_argv += ["--goal", args.goal]
    if args.branch:
        log_argv += ["--branch", args.branch]
    if args.phase:
        log_argv += ["--phase", args.phase]
    if args.run_id:
        log_argv += ["--run-id", args.run_id]
    if args.log_dir:  # log-event takes --log-dir, NOT --state-dir
        log_argv += ["--log-dir", args.log_dir]
    code, _ = _run(state, log_argv)
    if code not in (0, None):
        _rollback(remove_state=True)  # state-init succeeded above → remove what we made
        sys.stderr.write(f"begin failed at log (code {code}); claim + state rolled back.\n")
        return code or 1

    print(json.dumps({
        "task": task,
        "branch": args.branch,
        "worktree": args.worktree,
        "track": args.track,
        "claimed": True,
    }))
    return 0


# --------------------------------------------------------------------------
# end
# --------------------------------------------------------------------------
def cmd_end(args):
    """Completion teardown: release claim + archive state + log session_end (DD1).

    ``/openup-create-handoff`` does NOT call this — a handoff keeps its lease/state
    so the lane resumes. This is ``/openup-complete-task`` §7b.
    """
    task = args.task_id
    claims_flags = []
    if args.claims_dir:
        claims_flags += ["--claims-dir", args.claims_dir]
    state_flags = []
    if args.state_dir:
        state_flags += ["--state-dir", args.state_dir]

    # 1. Archive the live iteration state to the change folder (validates first).
    archive_code, _ = _run(state, ["archive", args.archive_to] + state_flags)
    if archive_code not in (0, None):
        sys.stderr.write(
            f"end: refusing to tear down — state archive failed (code {archive_code}). "
            f"Claim left intact.\n"
        )
        return archive_code or 1

    # 2. Log session_end (state file is gone now; log-event does not need it).
    log_argv = ["log-event", "--event", "session_end", "--task-id", task]
    if args.branch:
        log_argv += ["--branch", args.branch]
    if args.log_dir:  # log-event takes --log-dir, NOT --state-dir
        log_argv += ["--log-dir", args.log_dir]
    _run(state, log_argv)

    # 3. Release the claim (idempotent). Worktree removal stays in the skill.
    _run(claims, ["release", "--task-id", task] + (["--no-push"] if args.no_push else [])
         + claims_flags)

    print(json.dumps({"task": task, "status": args.status, "released": True}))
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def build_parser():
    p = argparse.ArgumentParser(
        prog="openup-session.py",
        description="Atomic OpenUP session lifecycle (claim + state + log).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    b = sub.add_parser("begin", help="Atomically acquire claim + state + log for a lane.")
    b.add_argument("--task-id", required=True)
    b.add_argument("--session-id", default=None)
    b.add_argument("--branch", default=None)
    b.add_argument("--worktree", default=None)
    b.add_argument("--iteration", required=True, type=int)
    b.add_argument("--phase", required=True)
    b.add_argument("--track", required=True)
    b.add_argument("--plan", default=None)
    b.add_argument("--goal", default=None)
    b.add_argument("--run-id", default=None)
    b.add_argument("--touches", default=None)
    b.add_argument("--depends-on", default=None)
    b.add_argument("--iterations-since-retro", type=int, default=None)
    b.add_argument("--reap", action="store_true",
                   help="Live-reap stale leases at begin (default: dry-run + warn only).")
    b.add_argument("--stale-after", type=int, default=DEFAULT_STALE_AFTER,
                   help=f"Stale-heartbeat threshold in seconds (default {DEFAULT_STALE_AFTER}).")
    b.add_argument("--no-push", action="store_true",
                   help="Local-only claim (skip git-ref push; used by tests).")
    b.add_argument("--force", action="store_true", help="Overwrite an existing state file.")
    b.add_argument("--claims-dir", default=None)
    b.add_argument("--state-dir", default=None)
    b.add_argument("--log-dir", default=None)
    b.set_defaults(func=cmd_begin)

    e = sub.add_parser("end", help="Completion teardown: archive state + release claim + log.")
    e.add_argument("--task-id", required=True)
    e.add_argument("--archive-to", required=True,
                   help="Path to archive .openup/state.json into (e.g. docs/changes/T-NNN/state.json).")
    e.add_argument("--status", choices=["done", "handoff"], default="done")
    e.add_argument("--branch", default=None)
    e.add_argument("--no-push", action="store_true")
    e.add_argument("--claims-dir", default=None)
    e.add_argument("--state-dir", default=None)
    e.add_argument("--log-dir", default=None)
    e.set_defaults(func=cmd_end)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
