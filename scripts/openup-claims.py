#!/usr/bin/env python3
"""OpenUP worktree-claim helper (T-009).

Live lease claims for parallel work. One JSON file per claim under the git
*common* dir at ``<git-common-dir>/openup/claims/T-NNN.json`` — shared across
all linked worktrees of the repo, never committed (it lives under ``.git/``).

Design rules (mirror scripts/openup-state.py):
  * Deterministic. Never invokes a model.
  * Python standard library only.
  * Claims NEVER expire (T-009 design D1): every present claim counts in the
    live collision set regardless of age and blocks an overlapping claim until
    a human removes the file (``rm`` is the sole recovery — D2, no ``--steal``).
  * The claim file carries its own ``touches`` (D7), copied from the task's
    frontmatter at claim time, so pre-flight is a PURE claim-file read and never
    joins back to frontmatter at enforcement time.
  * Pre-flight checks DEPENDENCIES FIRST, then collision (Q4): a dep-blocked
    task is never collision-evaluated.
  * Collision uses the T-008 path-segment-prefix algorithm (T-008 design D2).

Task-ID reservation (T-031) lives here too: parallel planning lanes used to
allocate IDs by scanning local state for the highest existing ID — two lanes
scanning concurrently (or against a stale trunk) both got ``T-{n+1}`` and
collided at merge. ``reserve-id`` closes that race: one reservation file per
ID under ``<claims-dir>/ids/``, created atomically (exclusive hard-link), with
the candidate drawn from max(repo scan ∪ origin/main roadmap ∪ live
reservations) + 1. Reservations follow claim rules: never expire, harmless
once the ID lands on trunk (allocation also scans the repo), ``release-id``
or ``rm`` frees an abandoned one.

Usage:
  python3 scripts/openup-claims.py <subcommand> [options]

Subcommands:
  preflight   Check deps + collision for a task WITHOUT writing a claim.
  claim       Run pre-flight, then atomically write the claim file.
  release     Delete a task's claim file (idempotent).
  list        Print all live claims (JSON array).
  get         Print one task's claim (or exit 5 if absent).
  dir         Print the resolved claims directory.
  reserve-id  Atomically reserve the next free task ID (or a requested one).
  next-id     Print the ID reserve-id would allocate; writes nothing.
  release-id  Delete an ID reservation (idempotent).
  list-ids    Print all live ID reservations (JSON array).

Exit codes:
  0  success / pre-flight passed
  2  argparse / usage error
  3  refused: an unmet dependency (pre-flight, deps first)
  4  refused: a touches collision with a live claim
  5  claim not found (get)
  6  refused: task already claimed/reserved by a DIFFERENT session, or a
     requested ID is already in use in the repo
  7  bad input (e.g. cannot resolve task touches, malformed task ID)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

EXIT_OK = 0
EXIT_DEP_UNMET = 3
EXIT_COLLISION = 4
EXIT_NOT_FOUND = 5
EXIT_OTHER_OWNER = 6
EXIT_BAD_INPUT = 7

SATISFIED_DEP_STATUSES = {"done", "verified", "completed"}


# --------------------------------------------------------------------------
# Git / path resolution
# --------------------------------------------------------------------------
def _git(args, cwd=None):
    """Run a git command, return stripped stdout ('' on failure)."""
    try:
        out = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def repo_root(cwd=None) -> Path:
    top = _git(["rev-parse", "--show-toplevel"], cwd)
    return Path(top) if top else Path.cwd()


def claims_dir(cwd=None, override=None) -> Path:
    """Resolve <git-common-dir>/openup/claims, honoring an explicit override.

    ``git rev-parse --git-common-dir`` returns the dir shared by all linked
    worktrees (so two worktrees of one repo see the SAME claims). It may be
    relative (``.git``) — resolve it against the repo root.
    """
    if override:
        return Path(override).expanduser().resolve()
    common = _git(["rev-parse", "--git-common-dir"], cwd)
    if not common:
        # Not a git repo (or git missing): fall back to a local .git path so
        # tests / odd environments still get a deterministic location.
        common = str((repo_root(cwd) / ".git"))
    p = Path(common)
    if not p.is_absolute():
        p = (repo_root(cwd) / p).resolve()
    return p / "openup" / "claims"


# --------------------------------------------------------------------------
# Minimal frontmatter parser (focused on coordination fields)
# --------------------------------------------------------------------------
def _strip_scalar(v: str):
    v = v.strip()
    if "#" in v:  # strip trailing inline comment (paths/ids contain no '#')
        v = v.split("#", 1)[0].strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v


def _parse_inline_list(v: str):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [_strip_scalar(x) for x in inner.split(",") if _strip_scalar(x)]
    return None


def parse_frontmatter(plan_path: Path) -> dict:
    """Parse the YAML frontmatter block of a plan.md into a dict.

    Handles exactly the shapes the coordination frontmatter uses: ``key: value``
    scalars, inline lists ``key: [a, b]``, and block lists (``key:`` then
    indented ``- item`` lines, with optional ``# comment`` suffixes).
    """
    text = plan_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    # find closing fence
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}

    data = {}
    i = 1
    while i < end:
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        if ":" not in raw:
            i += 1
            continue
        key, _, rest = raw.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest == "":
            # possible block list on following indented '- ' lines
            items = []
            j = i + 1
            while j < end:
                nxt = lines[j]
                stripped = nxt.strip()
                if stripped.startswith("- "):
                    items.append(_strip_scalar(stripped[2:]))
                    j += 1
                elif stripped == "" or nxt.startswith("#"):
                    j += 1
                else:
                    break
            data[key] = items
            i = j
            continue
        inline = _parse_inline_list(rest)
        if inline is not None:
            data[key] = inline
        else:
            data[key] = _strip_scalar(rest)
        i += 1
    return data


def find_task_plan(task_id: str, root: Path):
    """Locate the plan.md whose frontmatter id == task_id (active or archived)."""
    changes = root / "docs" / "changes"
    if not changes.exists():
        return None
    for plan in changes.rglob("plan.md"):
        fm = parse_frontmatter(plan)
        if fm.get("id") == task_id:
            return plan, fm
    return None


def roadmap_status(task_id: str, root: Path):
    """Best-effort status of a task from the roadmap table (human view)."""
    rm = root / "docs" / "roadmap.md"
    if not rm.exists():
        return None
    for line in rm.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells:
            continue
        # id cell may be a markdown link like [T-001](path)
        cell0 = cells[0]
        if task_id in cell0 and len(cells) >= 3:
            return cells[2].split()[0].lower()  # e.g. "completed (2026-..)" -> completed
    return None


def dep_satisfied(dep_id: str, root: Path):
    """(satisfied, reason). A dep is satisfied iff its status is done/verified."""
    found = find_task_plan(dep_id, root)
    if found:
        status = (found[1].get("status") or "").lower()
        if status in SATISFIED_DEP_STATUSES:
            return True, f"{dep_id} {status}"
        return False, f"{dep_id} is {status or 'unknown'} (needs done/verified)"
    rstat = roadmap_status(dep_id, root)
    if rstat in SATISFIED_DEP_STATUSES:
        return True, f"{dep_id} {rstat} (roadmap)"
    if rstat:
        return False, f"{dep_id} is {rstat} (roadmap; needs done/verified)"
    return False, f"{dep_id} not found in change folders or roadmap"


# --------------------------------------------------------------------------
# Collision (T-008 design D2: path-segment-prefix)
# --------------------------------------------------------------------------
def _norm(p: str) -> str:
    p = p.strip()
    if p.startswith("./"):
        p = p[2:]
    while "//" in p:
        p = p.replace("//", "/")
    return p


def seg_prefix_collide(a: str, b: str) -> bool:
    """True iff two paths share a prefix on a path-segment boundary.

    docs/changes/  vs docs/changes/T-002/  -> True  (prefix on '/').
    docs/changes/  vs docs/changesets/     -> False (segment differs).
    a/b            vs a/b                   -> True  (identical).
    """
    a, b = _norm(a), _norm(b)
    if not a or not b:
        return False
    if a == b:
        return True
    a2 = a if a.endswith("/") else a + "/"
    b2 = b if b.endswith("/") else b + "/"
    return a2.startswith(b2) or b2.startswith(a2)


def touches_overlap(touches_a, touches_b):
    """Return the list of (pa, pb) pairs that collide between two touch lists."""
    hits = []
    for pa in touches_a or []:
        for pb in touches_b or []:
            if seg_prefix_collide(pa, pb):
                hits.append((pa, pb))
    return hits


# --------------------------------------------------------------------------
# Claim file IO
# --------------------------------------------------------------------------
def claim_file(task_id: str, cdir: Path) -> Path:
    return cdir / f"{task_id}.json"


def read_claim(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def live_claims(cdir: Path):
    """All readable claim files as dicts. Corrupt files are surfaced as
    placeholders so pre-flight fails closed rather than treating them as free."""
    out = []
    if not cdir.exists():
        return out
    for fp in sorted(cdir.glob("*.json")):
        data = read_claim(fp)
        if data is None:
            # fail-closed: a corrupt claim occupies its task surface
            data = {"task_id": fp.stem, "session_id": None,
                    "touches": [], "_corrupt": True}
        out.append(data)
    return out


def write_claim_atomic(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.stem}.json.tmp"
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)  # atomic within the same directory


# --------------------------------------------------------------------------
# Task-ID reservation (T-031)
# --------------------------------------------------------------------------
def ids_dir(cdir: Path) -> Path:
    """Reservations live in a subdir so ``live_claims`` (cdir/*.json) never
    mistakes a reservation for a surface claim."""
    return cdir / "ids"


def _id_re(prefix: str):
    return re.compile(re.escape(prefix) + r"(\d+)")


def used_seqs_in_repo(root: Path, prefix: str):
    """Every ID sequence number already used in the repo.

    Sources (union — an ID seen anywhere is taken):
      * ``docs/changes/*/plan.md`` + ``docs/changes/archive/*/plan.md``
        frontmatter ``id`` (the canonical spec location);
      * ``docs/roadmap.md`` full text (IDs exist there before any spec
        folder does — maintenance rows, backlog mentions);
      * ``origin/main:docs/roadmap.md`` when that ref exists locally
        (stale-checkout guard: an ID merged to trunk is taken even if this
        worktree hasn't rebased; pure local read, never fetches).
    """
    pat = _id_re(prefix)
    seqs = set()
    changes = root / "docs" / "changes"
    if changes.exists():
        for plan in changes.rglob("plan.md"):
            m = pat.fullmatch(parse_frontmatter(plan).get("id") or "")
            if m:
                seqs.add(int(m.group(1)))
    texts = []
    rm = root / "docs" / "roadmap.md"
    if rm.exists():
        try:
            texts.append(rm.read_text(encoding="utf-8"))
        except OSError:
            pass
    trunk_view = _git(["show", "origin/main:docs/roadmap.md"], cwd=root)
    if trunk_view:
        texts.append(trunk_view)
    for text in texts:
        for m in pat.finditer(text):
            seqs.add(int(m.group(1)))
    return seqs


def reserved_seqs(idir: Path, prefix: str):
    """Sequence numbers held by live reservation files (any session's)."""
    pat = _id_re(prefix)
    seqs = set()
    if not idir.exists():
        return seqs
    for fp in idir.glob("*.json"):
        m = pat.fullmatch(fp.stem)
        if m:
            seqs.add(int(m.group(1)))
    return seqs


def reservation_file(task_id: str, idir: Path) -> Path:
    return idir / f"{task_id}.json"


def create_reservation_exclusive(path: Path, payload: dict) -> bool:
    """Atomically create the reservation WITH its content, or fail.

    Write to a tmp file, then hard-link it to the final name: the link either
    materializes the complete file or raises FileExistsError — a concurrent
    reader can never observe a half-written reservation, and two racing
    writers can never both win the same ID.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.stem}.{os.getpid()}.tmp"
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    try:
        os.link(tmp, path)
        return True
    except FileExistsError:
        return False
    finally:
        tmp.unlink(missing_ok=True)


def next_free_seq(root: Path, idir: Path, prefix: str) -> int:
    taken = used_seqs_in_repo(root, prefix) | reserved_seqs(idir, prefix)
    return max(taken, default=0) + 1


def format_id(prefix: str, seq: int, pad: int) -> str:
    return f"{prefix}{seq:0{pad}d}"


# --------------------------------------------------------------------------
# Pre-flight
# --------------------------------------------------------------------------
def resolve_task_inputs(args, root: Path):
    """Resolve (touches, depends_on) for the claiming task — from CLI overrides
    or the task's own plan.md frontmatter (D7: touches copied from frontmatter)."""
    touches = None
    deps = None
    if args.touches is not None:
        touches = [t for t in args.touches.split(",") if t.strip()]
    if getattr(args, "depends_on", None) is not None:
        deps = [d for d in args.depends_on.split(",") if d.strip()]
    if touches is None or deps is None:
        found = find_task_plan(args.task_id, root)
        if found:
            fm = found[1]
            if touches is None:
                touches = [_norm(t) for t in fm.get("touches", [])]
            if deps is None:
                deps = list(fm.get("depends-on", []))
        else:
            if touches is None:
                touches = []
            if deps is None:
                deps = []
    return touches, deps


def preflight(task_id, touches, deps, cdir, root):
    """Return (exit_code, message). 0 = clear.

    Order (Q4): dependencies first; only if all satisfied, check collision.
    """
    # 1. Dependencies first.
    for dep in deps:
        ok, reason = dep_satisfied(dep, root)
        if not ok:
            return EXIT_DEP_UNMET, f"BLOCKED: dependency {reason}"

    # 2. Collision against every OTHER live claim (claims never expire — D1).
    for claim in live_claims(cdir):
        if claim.get("task_id") == task_id:
            continue  # don't collide with our own existing claim
        if claim.get("_corrupt"):
            # Fail-closed (D8): a corrupt claim's surface is unknowable, so we
            # cannot prove the new claim is safe — refuse until a human fixes it.
            return EXIT_COLLISION, (
                f"REFUSED (fail-closed): corrupt claim file for "
                f"{claim.get('task_id')} — coordination state is unreadable. "
                f"Inspect/remove {claim_file(claim.get('task_id'), cdir)} first."
            )
        hits = touches_overlap(touches, claim.get("touches", []))
        if hits:
            owner_task = claim.get("task_id", "?")
            owner_sess = claim.get("session_id") or "unknown-session"
            corrupt = " (corrupt claim file — fail-closed)" if claim.get("_corrupt") else ""
            paths = ", ".join(sorted({f"{a}~{b}" if a != b else a for a, b in hits}))
            return EXIT_COLLISION, (
                f"COLLISION: surface [{paths}] is owned by {owner_task} "
                f"(session {owner_sess}){corrupt}. "
                f"Free it with: rm {claim_file(owner_task, cdir)}"
            )
    return EXIT_OK, "READY: no unmet dependency, no collision"


# --------------------------------------------------------------------------
# Subcommands
# --------------------------------------------------------------------------
def cmd_dir(args):
    print(claims_dir(override=args.claims_dir))
    return EXIT_OK


def cmd_preflight(args):
    root = repo_root()
    cdir = claims_dir(override=args.claims_dir)
    touches, deps = resolve_task_inputs(args, root)
    code, msg = preflight(args.task_id, touches, deps, cdir, root)
    (print if code == EXIT_OK else lambda m: sys.stderr.write(m + "\n"))(msg)
    return code


def cmd_claim(args):
    root = repo_root()
    cdir = claims_dir(override=args.claims_dir)
    touches, deps = resolve_task_inputs(args, root)

    # Idempotent / ownership check for an existing claim on this task.
    existing = read_claim(claim_file(args.task_id, cdir))
    if existing and not args.force:
        if existing.get("session_id") == args.session_id:
            # same owner: refresh in place (no pre-flight needed — already ours)
            pass
        else:
            sys.stderr.write(
                f"REFUSED: {args.task_id} already claimed by session "
                f"{existing.get('session_id')}. Use 'release' or rm the file.\n"
            )
            return EXIT_OTHER_OWNER
    else:
        code, msg = preflight(args.task_id, touches, deps, cdir, root)
        if code != EXIT_OK:
            sys.stderr.write(msg + "\n")
            return code

    payload = {
        "task_id": args.task_id,
        "session_id": args.session_id,
        "branch": args.branch,
        "worktree": args.worktree,
        "claimed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "touches": touches,
    }
    write_claim_atomic(claim_file(args.task_id, cdir), payload)
    print(f"Claimed {args.task_id} -> {claim_file(args.task_id, cdir)}")
    return EXIT_OK


def cmd_release(args):
    cdir = claims_dir(override=args.claims_dir)
    fp = claim_file(args.task_id, cdir)
    if fp.exists():
        fp.unlink()
        print(f"Released {args.task_id}")
    else:
        print(f"No claim for {args.task_id} (already released)")  # idempotent
    return EXIT_OK


def cmd_list(args):
    cdir = claims_dir(override=args.claims_dir)
    print(json.dumps(live_claims(cdir), indent=2))
    return EXIT_OK


def cmd_get(args):
    cdir = claims_dir(override=args.claims_dir)
    data = read_claim(claim_file(args.task_id, cdir))
    if data is None:
        sys.stderr.write(f"No claim for {args.task_id}\n")
        return EXIT_NOT_FOUND
    print(json.dumps(data, indent=2))
    return EXIT_OK


def _id_root(args) -> Path:
    return Path(args.repo_root).resolve() if args.repo_root else repo_root()


def cmd_next_id(args):
    root = _id_root(args)
    idir = ids_dir(claims_dir(override=args.claims_dir))
    seq = next_free_seq(root, idir, args.prefix)
    print(format_id(args.prefix, seq, args.pad))
    return EXIT_OK


def cmd_reserve_id(args):
    root = _id_root(args)
    idir = ids_dir(claims_dir(override=args.claims_dir))

    def payload(task_id):
        return {
            "task_id": task_id,
            "session_id": args.session_id,
            "title": args.title or "",
            "reserved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    if args.task_id:
        # Explicit ID: validate the shape, refuse if the repo or another
        # session already holds it; idempotent for the same session.
        m = _id_re(args.prefix).fullmatch(args.task_id)
        if not m:
            sys.stderr.write(
                f"BAD ID: {args.task_id!r} does not match prefix "
                f"{args.prefix!r} + digits.\n"
            )
            return EXIT_BAD_INPUT
        if int(m.group(1)) in used_seqs_in_repo(root, args.prefix):
            sys.stderr.write(
                f"REFUSED: {args.task_id} is already in use in the repo "
                f"(changes folder, roadmap, or origin/main roadmap).\n"
            )
            return EXIT_OTHER_OWNER
        fp = reservation_file(args.task_id, idir)
        if create_reservation_exclusive(fp, payload(args.task_id)):
            print(f"Reserved {args.task_id} -> {fp}")
            return EXIT_OK
        existing = read_claim(fp)
        if existing and existing.get("session_id") == args.session_id:
            print(f"Reserved {args.task_id} -> {fp} (already ours)")
            return EXIT_OK
        owner = (existing or {}).get("session_id") or "unknown-session"
        sys.stderr.write(
            f"REFUSED: {args.task_id} already reserved by session {owner}. "
            f"Free it with: rm {fp}\n"
        )
        return EXIT_OTHER_OWNER

    # Auto-allocate: candidate from the union scan, exclusive-create, and on
    # a lost race simply advance — the loop terminates because every loss
    # means another lane permanently holds that sequence number.
    seq = next_free_seq(root, idir, args.prefix)
    while True:
        task_id = format_id(args.prefix, seq, args.pad)
        fp = reservation_file(task_id, idir)
        if create_reservation_exclusive(fp, payload(task_id)):
            print(task_id)
            return EXIT_OK
        seq += 1


def cmd_release_id(args):
    idir = ids_dir(claims_dir(override=args.claims_dir))
    fp = reservation_file(args.task_id, idir)
    if fp.exists():
        fp.unlink()
        print(f"Released ID {args.task_id}")
    else:
        print(f"No reservation for {args.task_id} (already released)")  # idempotent
    return EXIT_OK


def cmd_list_ids(args):
    idir = ids_dir(claims_dir(override=args.claims_dir))
    out = []
    if idir.exists():
        for fp in sorted(idir.glob("*.json")):
            data = read_claim(fp)
            if data is None:
                data = {"task_id": fp.stem, "session_id": None, "_corrupt": True}
            out.append(data)
    print(json.dumps(out, indent=2))
    return EXIT_OK


# --------------------------------------------------------------------------
# Argument parsing
# --------------------------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        prog="openup-claims.py",
        description="OpenUP worktree-claim helper (live leases for parallel work).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(sp):
        sp.add_argument(
            "--claims-dir",
            help="Override the claims dir (default: <git-common-dir>/openup/claims).",
        )

    def add_task_inputs(sp):
        sp.add_argument(
            "--touches",
            default=None,
            help="Comma-separated paths; overrides the task's frontmatter touches.",
        )
        sp.add_argument(
            "--depends-on",
            default=None,
            help="Comma-separated dep ids; overrides frontmatter depends-on.",
        )

    p_dir = sub.add_parser("dir", help="Print the resolved claims directory.")
    add_common(p_dir)
    p_dir.set_defaults(func=cmd_dir)

    p_pf = sub.add_parser("preflight", help="Check deps + collision; write nothing.")
    p_pf.add_argument("--task-id", required=True)
    add_task_inputs(p_pf)
    add_common(p_pf)
    p_pf.set_defaults(func=cmd_preflight)

    p_cl = sub.add_parser("claim", help="Pre-flight then atomically write the claim.")
    p_cl.add_argument("--task-id", required=True)
    p_cl.add_argument("--session-id", required=True)
    p_cl.add_argument("--branch", required=True)
    p_cl.add_argument("--worktree", required=True)
    add_task_inputs(p_cl)
    p_cl.add_argument(
        "--force", action="store_true",
        help="Skip the existing-owner check (re-claim). Pre-flight still runs.",
    )
    add_common(p_cl)
    p_cl.set_defaults(func=cmd_claim)

    p_rl = sub.add_parser("release", help="Delete a task's claim (idempotent).")
    p_rl.add_argument("--task-id", required=True)
    add_common(p_rl)
    p_rl.set_defaults(func=cmd_release)

    p_ls = sub.add_parser("list", help="Print all live claims (JSON array).")
    add_common(p_ls)
    p_ls.set_defaults(func=cmd_list)

    p_gt = sub.add_parser("get", help="Print one task's claim.")
    p_gt.add_argument("--task-id", required=True)
    add_common(p_gt)
    p_gt.set_defaults(func=cmd_get)

    def add_id_common(sp):
        add_common(sp)
        sp.add_argument(
            "--prefix", default="T-",
            help="ID prefix to allocate under (default: 'T-'; e.g. 'C3-' for "
                 "phase-iteration IDs).",
        )
        sp.add_argument(
            "--pad", type=int, default=3,
            help="Zero-pad width for the sequence number (default: 3 -> T-031).",
        )
        sp.add_argument(
            "--repo-root", default=None,
            help="Override the repo root scanned for used IDs (tests).",
        )

    p_ni = sub.add_parser(
        "next-id", help="Print the ID reserve-id would allocate; writes nothing."
    )
    add_id_common(p_ni)
    p_ni.set_defaults(func=cmd_next_id)

    p_ri = sub.add_parser(
        "reserve-id",
        help="Atomically reserve the next free task ID (or a requested one).",
    )
    p_ri.add_argument("--session-id", required=True)
    p_ri.add_argument(
        "--task-id", default=None,
        help="Reserve this specific ID instead of auto-allocating.",
    )
    p_ri.add_argument("--title", default=None, help="One-line task title (recorded).")
    add_id_common(p_ri)
    p_ri.set_defaults(func=cmd_reserve_id)

    p_li = sub.add_parser("release-id", help="Delete an ID reservation (idempotent).")
    p_li.add_argument("--task-id", required=True)
    add_common(p_li)
    p_li.set_defaults(func=cmd_release_id)

    p_ls_ids = sub.add_parser("list-ids", help="Print all live ID reservations.")
    add_common(p_ls_ids)
    p_ls_ids.set_defaults(func=cmd_list_ids)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
