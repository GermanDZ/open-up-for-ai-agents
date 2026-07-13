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
  top-n     Print up to N collision-free READY lanes (or exit 3).
  resolve   Read-only: the §0–§1 /openup-next decision as one JSON object
            (path ∈ resume|pick|assess-iteration|milestone-review|plan-iteration|noop).
            Writes nothing (T-065).
  status    Read-only superset diagnostic (active iteration + leases +
            pickable lanes + promotable next) (T-065).

Exit codes:
  0  success (refresh; or top found a pickable lane)
  2  argparse / usage error
  3  top: no pickable lane (clean stop — the reason is printed to stderr)
"""

import argparse
import contextlib
import importlib.util
import io
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

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


# Default stale-heartbeat threshold for the refresh-time reap. Mirrors
# openup-claims.py's `reap --stale-after` default (1800s = 30 min).
REAP_STALE_AFTER = 1800


def _reap_stale_leases(cdir, stale_after):
    """Live-reap heartbeat-stale leases before deriving the board (T-063).

    Delegates to openup-claims.py's `cmd_reap` (composition — the heartbeat-gated
    T-060 invariant is inherited, never re-implemented: claims with no
    last_heartbeat are skipped there). The reaper's stdout chatter is captured so
    it never pollutes the board JSON printed on stdout; a one-line notice is
    surfaced on stderr only when something was actually reaped, so a crashed
    session's stale lane self-heals to READY within one refresh — i.e. within one
    /openup-next cycle.
    """
    ns = SimpleNamespace(claims_dir=str(cdir), stale_after=stale_after, dry_run=False)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        claims.cmd_reap(ns)
    for line in buf.getvalue().splitlines():
        if line.startswith("reaped "):
            sys.stderr.write(f"[board refresh] {line}\n")


def cmd_refresh(args):
    root = resolve_root(args)
    cdir = resolve_cdir(args, root)
    if not getattr(args, "no_reap", False):
        _reap_stale_leases(cdir, getattr(args, "reap_stale_after", REAP_STALE_AFTER))
    board = build_board(root, cdir)
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


def cmd_top_n(args):
    """Return up to N mutually collision-free READY lanes as a JSON array (T-060).

    Selection is greedy in board priority order: a READY lane is included if its
    ``touches`` don't prefix-overlap the touches of any already-selected lane.
    Exits 0 with a JSON array (possibly ``[]`` when N=0); exits 3 when the board
    has no READY lanes at all.
    """
    root = resolve_root(args)
    board = build_board(root, resolve_cdir(args, root))
    write_board(board, resolve_out(args, root))

    ready = [lane for lane in board["lanes"] if is_pickable(lane)]
    if not ready:
        sys.stderr.write(none_pickable_reason(board) + "\n")
        return EXIT_NONE_PICKABLE

    n = args.n
    selected = []
    selected_touches = []  # flat list of touch sets for already-selected lanes

    for lane in ready:
        if len(selected) >= n:
            break
        # Re-read the plan frontmatter to get this lane's touches.  (build_board
        # strips internal-only fields so we cannot rely on them here.)
        plan_rel = lane.get("plan")
        if plan_rel:
            try:
                fm = claims.parse_frontmatter(root / plan_rel)
                lane_touches = [claims._norm(t) for t in fm.get("touches", [])]
            except OSError:
                lane_touches = []
        else:
            lane_touches = []

        collides = any(
            claims.touches_overlap(lane_touches, prev_touches)
            for prev_touches in selected_touches
        )
        if not collides:
            selected.append(lane)
            selected_touches.append(lane_touches)

    print(json.dumps(selected, indent=2, ensure_ascii=False))
    return EXIT_OK


# --------------------------------------------------------------------------
# partition — cluster work items into non-colliding iteration groups (T-079)
#
# Lifts the lane-collision machinery one level: given a set of committed work
# items, group them into the coarsest clusters such that any two items that
# `touches`-overlap OR stand in a `depends-on` relation land in the SAME cluster.
# The clusters are the connected components of that undirected graph — so distinct
# clusters are, by construction, mutually disjoint in `touches` AND dependency-free
# across clusters. That is exactly the property that makes them safe to run as
# CONCURRENT iterations (Plan Iteration mints one iteration per cluster; the board
# already un-scopes `pick` when several iteration prefixes are live — see
# _active_iteration_prefix). A single cluster is the common case and degenerates
# to today's one-iteration behavior — parallelism is discovered from the structure
# of the work, never forced. Pure + read-only (no write_board, no reap).
# --------------------------------------------------------------------------
def _natural_key(s):
    """Deterministic natural-ish sort key: split embedded digit runs so ``C3``
    sorts before ``C10`` and ``C3-002`` before ``C3-010``. Order-independent."""
    return [(1, int(t)) if t.isdigit() else (0, t)
            for t in re.split(r"(\d+)", str(s)) if t != ""]


def _read_workitem(root: Path, wid: str):
    """``(touches, depends-on)`` for a work item from its change-folder plan
    (``docs/changes/<id>/plan.md``). Missing folder → empty lists (an item with
    no declared surface collides with nothing and depends on nothing)."""
    plan = root / "docs" / "changes" / wid / "plan.md"
    if not plan.exists():
        return [], []
    fm = claims.parse_frontmatter(plan)
    touches = [claims._norm(t) for t in fm.get("touches", [])]
    deps = [str(d).strip() for d in fm.get("depends-on", [])]
    return touches, deps


def partition_items(items):
    """Connected-component clustering of work items over the
    ``touches``-overlap ∪ ``depends-on`` graph.

    ``items`` is an ordered list of ``{"id", "touches", "depends-on"}`` dicts.
    Two items share a cluster iff their ``touches`` prefix-overlap
    (``claims.touches_overlap`` — the SAME rule the write-fence enforces) or
    either lists the other in ``depends-on``. Returns a list of clusters, each a
    list of ids; members are sorted naturally and clusters are ordered by their
    lowest member — so the output is deterministic and independent of input
    ordering (Requirement 2)."""
    ids = []
    info = {}
    for it in items:
        wid = str(it.get("id", "")).strip()
        if not wid or wid in info:
            continue
        ids.append(wid)
        info[wid] = (
            [claims._norm(t) for t in (it.get("touches") or [])],
            [str(d).strip() for d in (it.get("depends-on") or [])],
        )

    # Union-find; keep the naturally-smallest id as each set's root so the
    # partition is stable regardless of the order items are presented in.
    parent = {wid: wid for wid in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        keep, drop = sorted((ra, rb), key=_natural_key)
        parent[drop] = keep

    for i, a in enumerate(ids):
        ta, da = info[a]
        for b in ids[i + 1:]:
            tb, db = info[b]
            if claims.touches_overlap(ta, tb) or b in da or a in db:
                union(a, b)

    clusters = {}
    for wid in ids:
        clusters.setdefault(find(wid), []).append(wid)
    out = [sorted(members, key=_natural_key) for members in clusters.values()]
    out.sort(key=lambda c: _natural_key(c[0]))
    return out


def cmd_partition(args):
    """Cluster work items into non-colliding iteration groups (read-only).

    Two input modes:
      * positional ids  → read ``touches``/``depends-on`` from each
        ``docs/changes/<id>/plan.md`` (cluster existing change folders).
      * ``--stdin``     → read a JSON array of ``{id, touches, depends-on}``
        (Plan Iteration partitions *planned* work items before assigning
        cluster-prefixed ids, so no change folder needs renaming).
    Prints a JSON array of clusters (each a list of ids) and exits 0.
    """
    if args.stdin:
        try:
            items = json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError) as exc:
            sys.stderr.write(f"partition: invalid JSON on stdin: {exc}\n")
            return EXIT_USAGE
        if not isinstance(items, list):
            sys.stderr.write("partition: --stdin expects a JSON array of items.\n")
            return EXIT_USAGE
    else:
        root = resolve_root(args)
        items = [
            {"id": wid, "touches": t, "depends-on": d}
            for wid in args.ids
            for (t, d) in [_read_workitem(root, wid)]
        ]
    print(json.dumps(partition_items(items), indent=2, ensure_ascii=False))
    return EXIT_OK


# --------------------------------------------------------------------------
# resolve / status — the §0–§1 precedence, computed once as read-only data (T-065)
#
# `resolve` folds the four inputs the model chains by hand every /openup-next
# cycle (resumable-input → active-iteration → top-pickable → roadmap-next) into
# ONE decision object. `status` is the superset diagnostic. Both are READ-ONLY:
# they never write board.json, never run the reap — only `refresh` writes.
# The individual verbs are *composed*, not re-implemented (agreement-by-
# construction): promote reuses openup-roadmap.py's selector, so resolve's
# promote pick is identical to `openup-roadmap.py next` on the same inputs.
# --------------------------------------------------------------------------
def _load_sibling(name, filename):
    """Import a hyphenated sibling script as a module (same pattern as `claims`)."""
    path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _active_iteration(root: Path):
    """The active lane from this worktree's ``.openup/state.json`` (T-065).

    Read-only: parses the state file directly rather than importing
    openup-state.py (whose module-level REPO_ROOT would not track ``root``).
    Returns ``{"task": id}`` or ``None`` (no state / no task / unreadable)."""
    sp = root / ".openup" / "state.json"
    if not sp.exists():
        return None
    try:
        data = json.loads(sp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    task = data.get("task_id")
    return {"task": task} if task else None


def _resumable_input(root: Path):
    """The first answered input-request whose lane can resume (T-033/T-065).

    Composes openup-input.py's ``find_resumable`` — the same list §0 reads.
    Returns ``{"task": id, "request": path}`` or ``None``."""
    inp = _load_sibling("openup_input", "openup-input.py")
    rows = inp.find_resumable(root)
    if rows:
        task, req = rows[0]
        return {"task": task, "request": req}
    return None


def _promote_next(root: Path, cdir: Path):
    """The next promotable roadmap task (§1c), via openup-roadmap.py (T-064).

    Read-only composition: invokes ``cmd_next`` with stdout/stderr captured so
    the board's stdout stays clean. Returns ``(entry_or_None, reason)`` — the
    reason is roadmap's own exhaustion message when nothing is promotable."""
    rm = _load_sibling("openup_roadmap", "openup-roadmap.py")
    ns = SimpleNamespace(root=str(root), claims_dir=str(cdir))
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = rm.cmd_next(ns)
    if rc == EXIT_OK:
        try:
            return json.loads(out.getvalue()), None
        except json.JSONDecodeError:
            return None, "roadmap next: unparseable entry."
    return None, err.getvalue().strip() or "no promotable roadmap task."


# Iteration-prefixed lane ids (T-077): <PhaseLetter><ordinal>-<seq>, e.g. C3-001.
# A legacy task id (T-077) has no digit between the letter and the dash, so it
# does NOT match — its iteration prefix is None (unscoped, backward-compatible).
_ITER_PREFIX_RE = re.compile(r"^([A-Z]\d+)-\d+$")


def iteration_prefix(task_id):
    """The iteration id a lane belongs to (``C3`` for ``C3-001``), or None for a
    legacy/unprefixed task (``T-077``). Derived purely from the id — no state."""
    if not task_id:
        return None
    m = _ITER_PREFIX_RE.match(task_id)
    return m.group(1) if m else None


def _lifecycle_status(root: Path):
    """The full derived lifecycle status via openup-lifecycle.py (read-only,
    fail-open): ``{phase, cycle, criteria:[{id,desc,state}], …}`` or None if it
    cannot be computed — the resolver stays functional without it."""
    try:
        life = _load_sibling("openup_lifecycle", "openup-lifecycle.py")
        return life.compute_status(root, life.state_dir(root, None))
    except Exception:
        return None


def _current_phase(root: Path):
    """Derived current phase (or None). Thin front over _lifecycle_status."""
    status = _lifecycle_status(root)
    return status.get("phase") if status else None


def _milestone_exists(root: Path, phase, cycle) -> bool:
    """True if a milestone decision record already exists for ``phase``+``cycle``
    (any decision). Reuses lifecycle's record reader; fail-open to False."""
    if not phase:
        return False
    try:
        life = _load_sibling("openup_lifecycle", "openup-lifecycle.py")
        for rec in life.read_milestone_records(root):
            if rec.get("phase") == phase and rec.get("cycle") == cycle:
                return True
    except Exception:
        return False
    return False


def _phase_exit_ready(status) -> bool:
    """The phase is ready for a milestone go/no-go when no machine-checkable
    criterion is ``unmet`` (the ``human-judgment`` criteria are exactly what the
    milestone review resolves, so they do not block reaching it). A phase with
    no criteria (e.g. ``released``) is never 'ready' — nothing left to gate."""
    crits = (status or {}).get("criteria") or []
    if not crits:
        return False
    return all(c.get("state") != "unmet" for c in crits)


# --- Iteration-plan instance = the loop contract (T-077/T-078) ---------------
def _iteration_plan_instances(root: Path):
    """Every ``type: iteration-plan`` work-product instance under the two
    authoring locations (``docs/iteration-plans/`` and ``docs/phases/``).
    Returns ``(path, frontmatter)`` pairs. Read-only."""
    out = []
    for d in (root / "docs" / "iteration-plans", root / "docs" / "phases"):
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.md")):
            fm = claims.parse_frontmatter(p)
            if str(fm.get("type", "")).strip().lower() == "iteration-plan":
                out.append((p, fm))
    return out


def _work_item_done(root: Path, wid: str) -> bool:
    """A committed work item is delivered iff its change folder is archived, or
    its active plan carries a done/verified status. Unknown → not done."""
    if (root / "docs" / "changes" / "archive" / wid).is_dir():
        return True
    plan = root / "docs" / "changes" / wid / "plan.md"
    if plan.exists():
        fm = claims.parse_frontmatter(plan)
        return str(fm.get("status", "")).strip().lower() in DONE_STATUSES
    return False


def _has_assessment(plan_path: Path) -> bool:
    """True if the iteration-plan body carries an ``## Assessment`` section
    (written by /openup-assess-iteration) — the assessed marker."""
    try:
        for line in plan_path.read_text(encoding="utf-8").splitlines():
            if line.strip().lower() == "## assessment":
                return True
    except OSError:
        return False
    return False


def _active_iteration_plan(root: Path):
    """The minted phase-aware iteration currently in flight, if any.

    Identified by an iteration-plan instance whose committed work items
    (``traces-from``) include at least one **iteration-prefixed** lane id
    (``C3-001``) — legacy per-task plans trace to ``T-NNN`` / requirement ids and
    never match, so they cannot false-trigger. A ``verified``/``obsolete``
    instance is a closed iteration and is skipped. Returns
    ``{iteration, committed, all_done, assessed, plan}`` or None."""
    for p, fm in _iteration_plan_instances(root):
        if str(fm.get("status", "")).strip().lower() in {"verified", "obsolete"}:
            continue
        traces = fm.get("traces-from") or []
        if isinstance(traces, str):
            traces = [traces]
        committed = [str(t).strip() for t in traces
                     if _ITER_PREFIX_RE.match(str(t).strip())]
        if not committed:
            continue
        return {
            "iteration": iteration_prefix(committed[0]),
            "committed": committed,
            "all_done": all(_work_item_done(root, w) for w in committed),
            "assessed": _has_assessment(p),
            "plan": p.relative_to(root).as_posix(),
        }
    return None


def _active_iteration_prefix(cdir: Path):
    """The iteration whose lanes are currently being worked, derived from live
    leases. If exactly one iteration prefix is live, picks are scoped to it; if
    none (all legacy) or several (parallel iterations — T-079), no scoping."""
    prefixes = {
        iteration_prefix(c.get("task_id"))
        for c in claims.live_claims(cdir)
    }
    prefixes.discard(None)
    return next(iter(prefixes)) if len(prefixes) == 1 else None


def _decision(path, reason, lane=None, resumable_input=None,
              active_iteration=None, phase=None, cycle=None, legacy_path=None):
    return {
        "path": path,
        "lane": lane,
        "resumable_input": resumable_input,
        "active_iteration": active_iteration,
        "phase": phase,
        "cycle": cycle,
        # Back-compat alias during the T-077→T-078 transition: consumers still
        # keying on the old ``promote`` name find it here until openup-next is
        # rewired (T-078). None on every other path.
        "legacy_path": legacy_path,
        "reason": reason,
    }


def resolve_decision(root: Path, cdir: Path):
    """The §0–§1 precedence as one object (pure; no I/O side effects).

    Lifecycle-aware (carries the derived ``phase``) and iteration-scoped (T-077):
    while an iteration is active, §1b picks only lanes belonging to it, and the
    former §1c ``promote`` path is emitted as ``plan-iteration`` (carrying the
    phase) — Plan Iteration supersedes one-row-at-a-time promotion."""
    status = _lifecycle_status(root)
    phase = status.get("phase") if status else None
    cycle = status.get("cycle") if status else None
    # §0 — an answered input-request resumes its lane before any new claim.
    ri = _resumable_input(root)
    if ri:
        return _decision(
            "resume", f"answered input for {ri['task']} — resume it first.",
            lane={"task": ri["task"]}, resumable_input=ri, phase=phase, cycle=cycle)
    # §1a — an already-active iteration continues from its next unchecked box.
    ai = _active_iteration(root)
    if ai:
        return _decision(
            "resume", f"active iteration {ai['task']} — continue it.",
            lane={"task": ai["task"]}, active_iteration=ai, phase=phase, cycle=cycle)
    # §1b — the top pickable change-folder lane, iteration-scoped: while an
    # iteration is active, only its own lanes are pickable (a ready lane from a
    # different iteration waits its turn). Unscoped when no iteration is active.
    board = build_board(root, cdir)  # read-only: no write_board, no reap
    active_iter = _active_iteration_prefix(cdir)
    for lane in board["lanes"]:
        if not is_pickable(lane):
            continue
        if active_iter and iteration_prefix(lane["task"]) != active_iter:
            continue
        return _decision(
            "pick", f"top pickable lane {lane['task']}.", lane=lane,
            phase=phase, cycle=cycle)
    # §1c-assess (T-078) — a minted iteration whose committed work items are all
    # done but whose iteration plan has no assessment yet → run Assess Results.
    # Only fires for real phase-aware iterations (iteration-prefixed lanes); a
    # single-lane/promote flow has no such instance, so behavior is unchanged.
    iplan = _active_iteration_plan(root)
    if iplan and iplan["all_done"] and not iplan["assessed"]:
        return _decision(
            "assess-iteration",
            f"iteration {iplan['iteration']} exhausted — run Assess Results.",
            lane={"task": iplan["iteration"], "plan": iplan["plan"],
                  "next_action": "assess iteration"},
            phase=phase, cycle=cycle)
    # The next promotable roadmap task (needed by both §1c-milestone and §1d).
    entry, promote_reason = _promote_next(root, cdir)
    # §1c-milestone (T-078) — the roadmap is drained (nothing promotable), the
    # phase's exit criteria are met (no unmet machine criteria), and no milestone
    # record exists yet for this phase+cycle → pause for the human go/no-go.
    # Gating on "nothing promotable" (the same check §1d uses) keeps the loop
    # from reviewing a milestone while deliverable work still remains, and avoids
    # any disagreement between lifecycle's roadmap-clear and roadmap.py's next.
    # Records nothing itself — the loop delegates to /openup-phase-review.
    if (entry is None and _phase_exit_ready(status)
            and not _milestone_exists(root, phase, cycle)):
        return _decision(
            "milestone-review",
            f"{phase} phase exit criteria met (cycle {cycle}) — human go/no-go "
            f"needed before advancing; run /openup-phase-review.",
            lane={"task": phase, "next_action": "milestone review"},
            phase=phase, cycle=cycle)
    # §1d — no active iteration: plan the next iteration for the current phase
    # (the former single-row promote is its degenerate, single-work-item case).
    if entry:
        return _decision(
            "plan-iteration",
            f"plan a {phase or 'new'}-phase iteration "
            f"(next work item {entry['id']}).",
            lane={"task": entry["id"], "title": entry.get("title"),
                  "track": None, "next_action": "plan iteration + start"},
            phase=phase, cycle=cycle, legacy_path="promote")
    # §-noop — nothing pickable and nothing to plan.
    return _decision(
        "noop", f"{none_pickable_reason(board)} {promote_reason}".strip(),
        phase=phase, cycle=cycle)


def cmd_resolve(args):
    root = resolve_root(args)
    cdir = resolve_cdir(args, root)
    print(json.dumps(resolve_decision(root, cdir), indent=2, ensure_ascii=False))
    return EXIT_OK


def cmd_status(args):
    """Superset diagnostic for humans: active iteration + live leases +
    pickable lanes + promotable next. Read-only (no write, no reap)."""
    root = resolve_root(args)
    cdir = resolve_cdir(args, root)
    board = build_board(root, cdir)
    pickable = [lane for lane in board["lanes"] if is_pickable(lane)]
    leases = [
        {"task": c.get("task_id"), "branch": c.get("branch"),
         "worktree": c.get("worktree"), "last_heartbeat": c.get("last_heartbeat"),
         "corrupt": bool(c.get("_corrupt"))}
        for c in claims.live_claims(cdir)
    ]
    entry, _ = _promote_next(root, cdir)
    payload = {
        "active_iteration": _active_iteration(root),
        "leases": leases,
        "pickable": pickable,
        "promotable_next": ({"task": entry["id"], "title": entry.get("title")}
                            if entry else None),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return EXIT_OK


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
    p_refresh.add_argument(
        "--reap-stale-after", type=int, default=REAP_STALE_AFTER,
        help=f"Stale-heartbeat threshold (s) for the refresh-time reap "
             f"(default {REAP_STALE_AFTER}).",
    )
    p_refresh.add_argument(
        "--no-reap", action="store_true",
        help="Skip the refresh-time stale-lease reap.",
    )
    p_refresh.set_defaults(func=cmd_refresh)

    p_top = sub.add_parser("top", help="Print the top pickable lane (exit 3 if none).")
    add_common(p_top)
    p_top.set_defaults(func=cmd_top)

    p_top_n = sub.add_parser(
        "top-n",
        help="Print up to N collision-free READY lanes as a JSON array (T-060). "
             "Exit 3 if no READY lanes exist at all.",
    )
    p_top_n.add_argument(
        "n",
        type=int,
        metavar="N",
        help="Maximum number of lanes to return.",
    )
    add_common(p_top_n)
    p_top_n.set_defaults(func=cmd_top_n)

    p_partition = sub.add_parser(
        "partition",
        help="Cluster work items into non-colliding iteration groups (T-079): "
             "connected components over touches-overlap ∪ depends-on. Read-only; "
             "prints a JSON array of clusters (each a list of ids).",
    )
    p_partition.add_argument(
        "ids", nargs="*", metavar="ID",
        help="Work-item ids; touches/depends-on read from docs/changes/<id>/plan.md.",
    )
    p_partition.add_argument(
        "--stdin", action="store_true",
        help="Read a JSON array of {id, touches, depends-on} from stdin instead "
             "(partition planned items before assigning cluster-prefixed ids).",
    )
    add_common(p_partition)
    p_partition.set_defaults(func=cmd_partition)

    p_resolve = sub.add_parser(
        "resolve",
        help="Print the §0–§1 /openup-next decision as one read-only JSON object "
             "(path ∈ resume|pick|assess-iteration|milestone-review|plan-iteration|"
             "noop). Writes nothing.",
    )
    add_common(p_resolve)
    p_resolve.set_defaults(func=cmd_resolve)

    p_status = sub.add_parser(
        "status",
        help="Read-only superset diagnostic: active iteration + live leases + "
             "pickable lanes + promotable next.",
    )
    add_common(p_status)
    p_status.set_defaults(func=cmd_status)

    return parser


def main(argv=None):
    # Version staleness check (T-058): advisory warning, fail-open.
    try:
        _vc_path = Path(__file__).resolve().parent / "openup-version-check.py"
        _vc_spec = importlib.util.spec_from_file_location("openup_version_check", _vc_path)
        _vc = importlib.util.module_from_spec(_vc_spec)
        _vc_spec.loader.exec_module(_vc)  # type: ignore[union-attr]
        _vc.check_once(str(Path(__file__).resolve().parents[1]))
    except Exception:
        pass  # Version check never breaks the board.

    raw = list(sys.argv[1:] if argv is None else argv)
    # Default subcommand is `refresh` when the first token isn't a known command.
    if not raw or raw[0] not in {"refresh", "top", "top-n", "partition", "resolve", "status"}:
        raw = ["refresh"] + raw
    args = build_parser().parse_args(raw)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
