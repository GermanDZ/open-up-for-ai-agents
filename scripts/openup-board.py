#!/usr/bin/env python3
"""OpenUP execution board (T-017).

Derives ``.openup/board.json`` — a machine-readable queue of every active
delivery lane — from three deterministic inputs:

  * change-folder frontmatter   (``docs/changes/*/plan.md``, archive excluded)
  * live worktree leases        (``<git-common-dir>/openup/claims/T-NNN.json``)
  * Operations-checkbox state    (the first unchecked ``- [ ]`` in ``## Operations``)

It is the queue that ``/openup-next`` reads: the top pickable lane is the next
task to execute. The model NEVER authors ``board.json`` — "if a step is
deterministic, the harness does it." Identical inputs → byte-identical output
(no timestamps, no randomness in the payload).

Design rules (mirror scripts/openup-claims.py):
  * Deterministic. Never invokes a model. Python standard library only.
  * Agreement-by-construction: dependency satisfaction and the touches-collision
    test are *imported* from openup-claims.py, not re-implemented — so a lane the
    board calls ``ready`` is one ``openup-claims.py preflight`` would also clear.

Subcommands:
  refresh   (default) Regenerate ``.openup/board.json`` and print it.
  top       Regenerate, then print the single top pickable lane (or exit 3).

Exit codes:
  0  success (refresh; or top found a pickable lane)
  2  argparse / usage error
  3  top: no pickable lane (clean stop — the reason is printed to stderr)
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Reuse openup-claims.py (hyphenated filename → load via importlib). The board
# and the claim pre-flight MUST agree, so we share one implementation of
# frontmatter parsing, dependency resolution, and collision detection.
# --------------------------------------------------------------------------
_CLAIMS_PATH = Path(__file__).resolve().parent / "openup-claims.py"
_spec = importlib.util.spec_from_file_location("openup_claims", _CLAIMS_PATH)
claims = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(claims)  # type: ignore[union-attr]

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NONE_PICKABLE = 3

# Statuses that mean "this lane is finished" — excluded from the board.
DONE_STATUSES = {"done", "verified", "completed"}

CHECKBOX_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s+(.*)$")
ROLE_TAG_RE = re.compile(r"^\((?P<role>[a-z][a-z-]*)\)\s*(?P<rest>.*)$")

PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
STATE_RANK = {
    "ready": 0,
    "in-progress": 1,
    "elsewhere": 2,  # leased in another worktree, plan not on this tree (T-049)
    "colliding": 3,
    "blocked": 4,
    "suspended": 5,
    "deferred": 6,
}


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------
def active_plans(root: Path):
    """Every non-archived change-folder plan: ``docs/changes/*/plan.md`` (one
    level deep; ``docs/changes/archive/`` is excluded — those lanes are done)."""
    changes = root / "docs" / "changes"
    out = []
    if not changes.exists():
        return out
    for sub in sorted(changes.iterdir()):
        if not sub.is_dir() or sub.name == "archive":
            continue
        plan = sub / "plan.md"
        if plan.exists():
            out.append(plan)
    return out


def parse_operations(plan_text: str):
    """Return ``(next_action, hat)`` from the ``## Operations`` checkbox list.

    ``next_action`` is the text of the FIRST unchecked ``- [ ]`` step (role tag
    stripped); ``hat`` is its optional leading ``(role)`` tag, defaulting to
    ``developer``. Legacy numbered Operations (no checkboxes) → ``(None, None)``,
    never an error.
    """
    in_ops = False
    for line in plan_text.splitlines():
        if line.startswith("## "):
            in_ops = line.strip().lower() == "## operations"
            continue
        if not in_ops:
            continue
        m = CHECKBOX_RE.match(line)
        if not m:
            continue
        checked = m.group(1).lower() == "x"
        if checked:
            continue
        text = m.group(2).strip()
        rm = ROLE_TAG_RE.match(text)
        if rm:
            return rm.group("rest").strip(), rm.group("role")
        return text, "developer"
    return None, None


def lease_for(task_id: str, live):
    """The live lease dict for ``task_id`` (trimmed), or ``None``."""
    for claim in live:
        if claim.get("task_id") == task_id and not claim.get("_corrupt"):
            return {
                "session_id": claim.get("session_id"),
                "branch": claim.get("branch"),
                "worktree": claim.get("worktree"),
                "claimed_at": claim.get("claimed_at"),
            }
    return None


def request_status(req_rel: str, root: Path):
    """Status of the input-request at ``req_rel`` (path relative to ``root``), or
    ``None`` if the field is empty or the file is missing/unreadable. A stale
    pointer (request already processed + archived) reads as ``None``."""
    if not req_rel:
        return None
    p = root / req_rel
    if not p.is_file():
        return None
    fm = claims.parse_frontmatter(p)
    return (fm.get("status") or "").lower() or None


def is_suspended(awaiting_input: str, root: Path) -> bool:
    """A lane is suspended iff its ``awaiting-input`` request is still ``pending``
    (an open question for a human). Once the request is ``answered`` the lane is
    no longer suspended — it is resumable, and /openup-next picks it up via the
    Step-0 answered-check (see openup-input.py resumable)."""
    return request_status(awaiting_input, root) == "pending"


def collider_for(task_id: str, touches, live):
    """Task id of a live lease (owned by another task) whose ``touches`` overlap
    this lane's, or ``None``. Mirrors the pre-flight collision rule."""
    for claim in live:
        owner = claim.get("task_id")
        if owner == task_id:
            continue  # never collide with our own lease
        if claim.get("_corrupt"):
            return owner  # fail-closed: unknowable surface blocks us
        if claims.touches_overlap(touches, claim.get("touches", [])):
            return owner
    return None


# --------------------------------------------------------------------------
# Lane assembly
# --------------------------------------------------------------------------
def build_lane(plan_path: Path, root: Path, live):
    fm = claims.parse_frontmatter(plan_path)
    task_id = fm.get("id")
    if not task_id:
        return None
    status = (fm.get("status") or "").lower()
    if status in DONE_STATUSES:
        return None  # finished lanes are not queued

    touches = [claims._norm(t) for t in fm.get("touches", [])]
    deps = list(fm.get("depends-on", []))
    depends_ok = all(claims.dep_satisfied(d, root)[0] for d in deps)

    lease = lease_for(task_id, live)
    collides_with = collider_for(task_id, touches, live)

    awaiting_input = fm.get("awaiting-input")
    suspended = is_suspended(awaiting_input, root)

    next_action, hat = parse_operations(plan_path.read_text(encoding="utf-8"))

    state = classify(status, lease, depends_ok, collides_with, suspended)

    lane = {
        "task": task_id,
        "title": fm.get("title"),
        "track": fm.get("track"),  # often None until iteration start
        "state": state,
        "lease": lease,
        "hat": hat,
        "next_action": next_action,
        "plan": str(plan_path.relative_to(root)).replace("\\", "/"),
        "collides_with": collides_with,
        "depends_ok": depends_ok,
        # The open input-request blocking this lane (only while suspended);
        # None otherwise.
        "awaiting_input": awaiting_input if suspended else None,
    }
    # Carried only for sorting; not part of the lane payload.
    lane["_priority"] = (fm.get("priority") or "medium").lower()
    return lane


def classify(status: str, lease, depends_ok: bool, collides_with, suspended=False):
    """Deterministic lane-state classification (see plan §Requirements 3)."""
    if status == "deferred":
        return "deferred"
    if suspended:
        # An open input-request (awaiting a human answer) outranks every other
        # not-pickable reason — it is the specific, actionable signal.
        return "suspended"
    if status == "blocked":
        return "blocked"  # author-asserted block; surfaced, never auto-promoted
    if lease is not None or status == "in-progress":
        return "in-progress"
    if not depends_ok:
        return "blocked"
    if collides_with is not None:
        return "colliding"
    return "ready"


def is_pickable(lane) -> bool:
    return (
        lane["state"] == "ready"
        and lane["lease"] is None
        and lane["depends_ok"]
        and lane["collides_with"] is None
    )


def sort_key(lane):
    return (
        0 if is_pickable(lane) else 1,
        STATE_RANK.get(lane["state"], 9),
        PRIORITY_RANK.get(lane.get("_priority", "medium"), 2),
        lane["task"],
    )


def orphan_lease_lane(claim):
    """Synthesize an ``elsewhere`` lane from a live lease that has no plan-derived
    lane on this tree (T-049). Its spec is committed on an unmerged branch / in
    another worktree, so the trunk checkout can't see the ``plan.md`` — but the
    lease (shared ``--git-common-dir``) proves the task is in flight. The lane is
    visible and collision-correct, but never pickable (``state != "ready"``)."""
    lane = {
        "task": claim.get("task_id"),
        "title": None,
        "track": None,
        "state": "elsewhere",
        "lease": {
            "session_id": claim.get("session_id"),
            "branch": claim.get("branch"),
            "worktree": claim.get("worktree"),
            "claimed_at": claim.get("claimed_at"),
        },
        "hat": None,
        "next_action": None,
        "plan": None,        # no spec on this tree — that is the whole point
        "collides_with": None,
        "depends_ok": True,  # unknowable locally; never consulted (not pickable)
        "awaiting_input": None,
    }
    lane["_priority"] = "medium"  # sort-only; stripped before return
    return lane


def build_board(root: Path, cdir: Path):
    live = claims.live_claims(cdir)
    lanes = [
        lane
        for plan in active_plans(root)
        if (lane := build_lane(plan, root, live)) is not None
    ]
    # A live lease whose task has no plan-derived lane is in flight elsewhere
    # (committed on an unmerged branch / another worktree). Surface it as an
    # ``elsewhere`` lane so a trunk board is not blind to it and the loop does
    # not re-promote it (T-049). Corrupt leases are skipped — they are already
    # surfaced fail-closed as colliders, never as workable lanes.
    claimed = {lane["task"] for lane in lanes}
    for claim in live:
        task_id = claim.get("task_id")
        if claim.get("_corrupt") or not task_id or task_id in claimed:
            continue
        lanes.append(orphan_lease_lane(claim))
        claimed.add(task_id)
    lanes.sort(key=sort_key)
    for lane in lanes:
        lane.pop("_priority", None)  # strip the sort-only field
    return {"lanes": lanes}


def write_board(board, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(board, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def none_pickable_reason(board) -> str:
    # ``elsewhere`` lanes are in flight in another worktree and have no spec on
    # this tree, so they are NOT local work that holds up the loop. Count them
    # apart from local plan-derived lanes: an elsewhere-only board must still
    # route /openup-next into its promote step (the roadmap may have promotable
    # work), exactly as an empty board did before T-049 — only now the in-flight
    # task is visible rather than invisible.
    local = {}
    elsewhere = 0
    for lane in board["lanes"]:
        if lane["state"] == "elsewhere":
            elsewhere += 1
        else:
            local[lane["state"]] = local.get(lane["state"], 0) + 1
    if not local:
        if not elsewhere:
            return "no active lanes — every change folder is done/archived or absent."
        return (
            f"no active local lanes ({elsewhere} in flight elsewhere) — "
            "roadmap may have promotable work."
        )
    parts = ", ".join(f"{n} {s}" for s, n in sorted(local.items()))
    if elsewhere:
        parts += f", {elsewhere} elsewhere"
    return f"no pickable lane ({parts})."


# --------------------------------------------------------------------------
# Subcommands
# --------------------------------------------------------------------------
def resolve_root(args) -> Path:
    return Path(args.root).resolve() if args.root else claims.repo_root()


def resolve_out(args, root: Path) -> Path:
    return Path(args.out).resolve() if args.out else root / ".openup" / "board.json"


def resolve_cdir(args, root: Path) -> Path:
    return claims.claims_dir(cwd=root, override=args.claims_dir)


def cmd_refresh(args):
    root = resolve_root(args)
    board = build_board(root, resolve_cdir(args, root))
    write_board(board, resolve_out(args, root))
    print(json.dumps(board, indent=2, ensure_ascii=False))
    return EXIT_OK


def cmd_top(args):
    root = resolve_root(args)
    board = build_board(root, resolve_cdir(args, root))
    write_board(board, resolve_out(args, root))
    for lane in board["lanes"]:
        if is_pickable(lane):
            print(json.dumps(lane, indent=2, ensure_ascii=False))
            return EXIT_OK
    sys.stderr.write(none_pickable_reason(board) + "\n")
    return EXIT_NONE_PICKABLE


# --------------------------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        prog="openup-board.py",
        description="Derive .openup/board.json (the /openup-next execution queue).",
    )
    sub = parser.add_subparsers(dest="cmd")

    def add_common(sp):
        sp.add_argument("--root", help="Repo root override (default: git toplevel).")
        sp.add_argument("--claims-dir", help="Override the leases dir (tests).")
        sp.add_argument("--out", help="Board output path (default: .openup/board.json).")

    p_refresh = sub.add_parser("refresh", help="Regenerate and print the board.")
    add_common(p_refresh)
    p_refresh.set_defaults(func=cmd_refresh)

    p_top = sub.add_parser("top", help="Print the top pickable lane (exit 3 if none).")
    add_common(p_top)
    p_top.set_defaults(func=cmd_top)

    return parser


def main(argv=None):
    raw = list(sys.argv[1:] if argv is None else argv)
    # Default subcommand is `refresh` when the first token isn't a known command.
    if not raw or raw[0] not in {"refresh", "top"}:
        raw = ["refresh"] + raw
    args = build_parser().parse_args(raw)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
