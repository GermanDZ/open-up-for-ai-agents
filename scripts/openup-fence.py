#!/usr/bin/env python3
"""OpenUP write-fence (T-024).

Deterministic guardrail that a lane's committed diff stays inside the surface
it claimed. Parallel-PR conflicts in shared process docs happen when a branch
writes files outside its lane — most often the shared views
(``docs/roadmap.md``, ``docs/project-status.md``) regenerated against a stale
trunk. The fence checks ``git diff --name-only <merge-base(base, HEAD)>..HEAD``
against an allowlist derived from the same inputs the claim pre-flight uses,
so it covers humans (via the ``pre-push`` hook / a PR check) and agents (via
the ``/openup-complete-task`` gate) identically.

Allowed for task T-NNN:
  * the task's ``touches`` — from its live claim file if present (D7: the
    claim is authoritative at enforcement time), else its plan frontmatter;
  * its own change folder ``docs/changes/T-NNN/`` and the archive destination
    ``docs/changes/archive/T-NNN/``;
  * lane-owned / append-only audit surfaces that never conflict:
    ``docs/agent-logs/`` (dated files + the merge=union JSONL),
    ``docs/status-notes/`` (sharded status entries), ``docs/explorations/``;
  * the shared derived views ``docs/roadmap.md`` / ``docs/project-status.md``
    (written by ``sync-status.py``) and ``docs/INDEX.md`` (the trace-web index,
    written by ``docs-index.py``) ONLY if the base ref is an ancestor of HEAD
    (the **fresh-base rule**: views may only be regenerated against the current
    trunk — otherwise rebase and re-run the generator), or unconditionally with
    ``--allow-views`` (used by complete-task immediately after it rebased).

Design rules (mirror scripts/openup-claims.py / openup-board.py):
  * Deterministic. Never invokes a model. Python standard library only.
  * Agreement-by-construction: frontmatter parsing, claim reading, and the
    path-segment-prefix match are *imported* from openup-claims.py, not
    re-implemented.
  * Fails open only when the fence is inapplicable (no base ref to diff
    against, e.g. a clone without the trunk) — and says so on stderr.

Subcommands:
  check     Validate the diff (default base: origin/main, fallback main).
  allowed   Print the resolved allowlist as JSON (debugging).

Exit codes:
  0  pass (or fence inapplicable — printed to stderr)
  2  argparse / usage error
  3  no task id resolvable (no --task-id and no .openup/state.json)
  8  fence violation (each offending file printed to stderr)
"""

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Reuse openup-claims.py (hyphenated filename -> load via importlib). The
# fence and the claim pre-flight MUST agree on what a task touches, so we
# share one implementation of frontmatter parsing, claim IO, and path match.
# --------------------------------------------------------------------------
_CLAIMS_PATH = Path(__file__).resolve().parent / "openup-claims.py"
_spec = importlib.util.spec_from_file_location("openup_claims", _CLAIMS_PATH)
claims = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(claims)  # type: ignore[union-attr]

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NO_TASK = 3
EXIT_VIOLATION = 8

# Shared derived views: regenerated ONLY against a fresh trunk, never hand-edited.
# roadmap.md / project-status.md are written by scripts/sync-status.py; INDEX.md
# (the trace-web index) by scripts/docs-index.py — all three are subject to the
# fresh-base rule below. (T-122/B8: INDEX.md joins the fenced views — its absence
# flagged a legitimate regeneration OUT OF LANE and caused the T-003 revert.)
VIEW_PATHS = ["docs/roadmap.md", "docs/project-status.md", "docs/INDEX.md"]

# Lane-owned / append-only surfaces every lane may write without conflicting:
# dated one-file-per-entry trees and the merge=union run log.
ALWAYS_ALLOWED = [
    "docs/agent-logs/",
    "docs/status-notes/",
    "docs/explorations/",
]


# --------------------------------------------------------------------------
# Git helpers
# --------------------------------------------------------------------------
def _git(args, cwd=None):
    try:
        out = subprocess.run(
            ["git"] + args, cwd=cwd, capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def resolve_base(explicit, cwd=None):
    """First ref that resolves among: --base, origin/main, main."""
    candidates = [explicit] if explicit else ["origin/main", "main"]
    for ref in candidates:
        if ref and _git(["rev-parse", "--verify", "--quiet", ref], cwd) is not None:
            return ref
    return None


def changed_files(base, cwd=None):
    """Repo-relative paths changed between merge-base(base, HEAD) and HEAD."""
    out = _git(["diff", "--name-only", f"{base}...HEAD"], cwd)
    if out is None:
        return None
    return [line for line in out.splitlines() if line.strip()]


def base_is_ancestor(base, cwd=None):
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", base, "HEAD"],
            cwd=cwd, capture_output=True, check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


# --------------------------------------------------------------------------
# Allowlist
# --------------------------------------------------------------------------
def resolve_task_id(args, root: Path):
    if args.task_id:
        return args.task_id
    sdir = Path(args.state_dir).expanduser().resolve() if args.state_dir \
        else root / ".openup"
    state = sdir / "state.json"
    if state.exists():
        try:
            return json.loads(state.read_text(encoding="utf-8")).get("task_id")
        except (OSError, json.JSONDecodeError):
            return None
    return None


def resolve_track(args, root: Path):
    """Read the active iteration's track from .openup/state.json (or None)."""
    sdir = Path(args.state_dir).expanduser().resolve() if args.state_dir \
        else root / ".openup"
    state = sdir / "state.json"
    if state.exists():
        try:
            return json.loads(state.read_text(encoding="utf-8")).get("track")
        except (OSError, json.JSONDecodeError):
            return None
    return None


def task_touches(task_id: str, root: Path, cdir: Path):
    """The task's touches — live claim first (D7), then plan frontmatter."""
    claim = claims.read_claim(claims.claim_file(task_id, cdir))
    if claim and claim.get("touches"):
        return [claims._norm(t) for t in claim["touches"]]
    found = claims.find_task_plan(task_id, root)
    if found:
        return [claims._norm(t) for t in found[1].get("touches", [])]
    return []


def build_allowlist(task_id: str, root: Path, cdir: Path, extra):
    allowed = list(ALWAYS_ALLOWED)
    allowed.append(f"docs/changes/{task_id}/")
    allowed.append(f"docs/changes/archive/{task_id}/")
    allowed.extend(task_touches(task_id, root, cdir))
    allowed.extend(claims._norm(p) for p in extra if p.strip())
    # de-dup, stable order
    seen, out = set(), []
    for p in allowed:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def is_allowed(path: str, allowlist) -> bool:
    return any(claims.seg_prefix_collide(path, entry) for entry in allowlist)


# --------------------------------------------------------------------------
# Subcommands
# --------------------------------------------------------------------------
def cmd_check(args) -> int:
    root = claims.repo_root()
    cdir = claims.claims_dir(override=args.claims_dir)

    task_id = resolve_task_id(args, root)
    if not task_id:
        sys.stderr.write(
            "openup-fence: no task id (--task-id missing and no "
            ".openup/state.json) — cannot resolve the lane's surface.\n"
        )
        return EXIT_NO_TASK

    base = resolve_base(args.base)
    if base is None:
        sys.stderr.write(
            "openup-fence: no base ref resolvable (tried "
            f"{args.base or 'origin/main, main'}) — fence inapplicable.\n"
        )
        return EXIT_OK

    files = changed_files(base)
    if files is None:
        sys.stderr.write("openup-fence: git diff failed — fence inapplicable.\n")
        return EXIT_OK
    if not files:
        print(f"openup-fence: {task_id} — no changes vs {base}.")
        return EXIT_OK

    extra = (args.allow or "").split(",")
    allowlist = build_allowlist(task_id, root, cdir, extra)
    fresh_base = base_is_ancestor(base)

    # Quick-track lanes have no plan.md, so their claim `touches` is empty. The
    # quick track is single-file / no-plan-gate by design, so a quick lane that
    # declared no surface is *unfenced* — its real edits are not flagged
    # out-of-lane (T-042 G2). It opts back into fencing by declaring `touches`
    # (re-claim) or passing `--allow`. View-freshness is orthogonal and still
    # enforced below.
    track = resolve_track(args, root)
    declared = bool(task_touches(task_id, root, cdir)) or any(
        e.strip() for e in extra
    )
    quick_unfenced = track == "quick" and not declared

    out_of_lane = []
    stale_views = []
    for f in files:
        f = claims._norm(f)
        if is_allowed(f, allowlist):
            continue
        if any(claims.seg_prefix_collide(f, v) for v in VIEW_PATHS):
            if args.allow_views or fresh_base:
                continue
            stale_views.append(f)
        elif quick_unfenced:
            continue
        else:
            out_of_lane.append(f)

    if not out_of_lane and not stale_views:
        if quick_unfenced:
            print(
                f"openup-fence: {task_id} — quick-track lane, unfenced "
                f"({len(files)} changed file(s), no declared `touches`; pass "
                f"`--allow`/declare touches to opt into fencing)."
            )
        else:
            print(
                f"openup-fence: {task_id} — {len(files)} changed file(s) "
                f"within lane (base {base})."
            )
        return EXIT_OK

    for f in out_of_lane:
        sys.stderr.write(
            f"OUT OF LANE: {f} — not in {task_id}'s touches, change folder, "
            "or a lane-owned surface. Either claim it (add to the task's "
            "frontmatter `touches` and re-claim) or move the edit to the "
            "task that owns it.\n"
        )
    for f in stale_views:
        sys.stderr.write(
            f"STALE VIEW: {f} — shared views may only be regenerated against "
            f"the current trunk, but {base} is not an ancestor of HEAD. "
            f"Rebase onto {base}, re-run `python3 scripts/sync-status.py`, "
            "and never hand-merge these files.\n"
        )
    return EXIT_VIOLATION


def cmd_allowed(args) -> int:
    root = claims.repo_root()
    cdir = claims.claims_dir(override=args.claims_dir)
    task_id = resolve_task_id(args, root)
    if not task_id:
        sys.stderr.write("openup-fence: no task id resolvable.\n")
        return EXIT_NO_TASK
    extra = (args.allow or "").split(",")
    payload = {
        "task": task_id,
        "allowed": build_allowlist(task_id, root, cdir, extra),
        "views": VIEW_PATHS,
        "views_rule": "fresh-base or --allow-views",
    }
    print(json.dumps(payload, indent=2))
    return EXIT_OK


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="openup-fence.py",
        description="Check that a lane's diff stays inside its claimed surface.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--task-id", help="Lane task id (default: .openup/state.json).")
        p.add_argument("--base", help="Trunk ref (default: origin/main, then main).")
        p.add_argument("--allow", help="Comma-separated extra allowed paths.")
        p.add_argument("--allow-views", action="store_true",
                       help="Allow the shared views regardless of base freshness "
                            "(complete-task passes this right after rebasing).")
        p.add_argument("--claims-dir", help="Override the claims directory (tests).")
        p.add_argument("--state-dir", help="Override the .openup directory (tests).")

    common(sub.add_parser("check", help="Validate the diff against the lane."))
    common(sub.add_parser("allowed", help="Print the resolved allowlist."))

    args = parser.parse_args(argv)
    if args.cmd == "check":
        return cmd_check(args)
    return cmd_allowed(args)


if __name__ == "__main__":
    sys.exit(main())
