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
  remote-check Advisory cross-machine branch-as-claim check (T-044); exit 9 on
              a remote duplicate, fail-open otherwise.
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
EXIT_REMOTE_DUP = 9  # a remote branch already encodes this task (T-044)

# --------------------------------------------------------------------------
# Git-ref distributed locking (T-056): push claims to refs/openup/claims/<id>
# so two agents on different machines cannot both claim the same task.
# All network operations are fail-open: if the remote is unreachable the
# behaviour is identical to today (local-only claims).
# --------------------------------------------------------------------------

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


def is_archived_plan(plan_path: Path, root: Path) -> bool:
    """True iff plan_path lives under ``docs/changes/archive/`` (i.e. the task
    has been completed/retired via /openup-complete-task, which git-mv's the
    change folder into the archive ring)."""
    try:
        rel = plan_path.resolve().relative_to((root / "docs" / "changes").resolve())
    except (ValueError, OSError):
        return False
    return len(rel.parts) > 0 and rel.parts[0] == "archive"


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
    """(satisfied, reason). A dep is satisfied iff its status is done/verified.

    Archived deps (T-048): a plan under ``docs/changes/archive/`` whose body
    ``status:`` was never bumped off a non-satisfied value (pre-T-042 archives,
    or a ``deferred`` plan later completed) must NOT false-block a downstream
    lane. For an archived plan we therefore defer to the roadmap — the human view
    of record — rather than trusting a stale body. Active (non-archived) plans
    stay authoritative: an ``in-progress`` *live* spec really is unmet.
    Archive presence alone is deliberately NOT enough (a genuinely-deferred plan
    can be archived); only a roadmap-satisfied row flips a stale archived plan.
    """
    found = find_task_plan(dep_id, root)
    if found:
        plan_path, fm = found
        status = (fm.get("status") or "").lower()
        if status in SATISFIED_DEP_STATUSES:
            return True, f"{dep_id} {status}"
        if is_archived_plan(plan_path, root):
            rstat = roadmap_status(dep_id, root)
            if rstat in SATISFIED_DEP_STATUSES:
                return True, (
                    f"{dep_id} {rstat} (roadmap; archived plan body "
                    f"'{status or 'unknown'}' is stale)"
                )
            if rstat:
                return False, f"{dep_id} is {rstat} (roadmap; archived)"
            return False, (
                f"{dep_id} is {status or 'unknown'} (archived; no roadmap row "
                f"to vouch completion)"
            )
        return False, f"{dep_id} is {status or 'unknown'} (needs done/verified)"
    rstat = roadmap_status(dep_id, root)
    if rstat in SATISFIED_DEP_STATUSES:
        return True, f"{dep_id} {rstat} (roadmap)"
    if rstat:
        return False, f"{dep_id} is {rstat} (roadmap; needs done/verified)"
    return False, f"{dep_id} not found in change folders or roadmap"


# --------------------------------------------------------------------------
# Archived-status migration (T-048): repair stale archived plans
# --------------------------------------------------------------------------
def migrate_archived_status(root: Path, satisfied_status: str = "done",
                            dry_run: bool = False):
    """Bump archived plans whose body ``status:`` is stale.

    A plan under ``docs/changes/archive/`` is *stale* when its body status is
    non-satisfied (e.g. ``in-progress``, ``deferred``) **but the roadmap row says
    it is completed** — i.e. the task really finished but the archive step never
    bumped the body (pre-T-042 archives, or a deferred plan later completed). Such
    a body false-blocks downstream deps via ``dep_satisfied``.

    Only roadmap-satisfied plans are touched: a genuinely-``deferred``/``cancelled``
    archived plan (roadmap not completed) is left as-is. Idempotent — a plan already
    at a satisfied status is skipped, so a second run changes zero files.

    Returns a list of ``(task_id, old_status, rel_path)`` for changed (or, in
    ``dry_run``, would-change) plans.
    """
    archive = root / "docs" / "changes" / "archive"
    changed = []
    if not archive.exists():
        return changed
    for plan in sorted(archive.rglob("plan.md")):
        fm = parse_frontmatter(plan)
        tid = fm.get("id")
        status = (fm.get("status") or "").lower()
        if not tid or status in SATISFIED_DEP_STATUSES:
            continue
        if roadmap_status(tid, root) not in SATISFIED_DEP_STATUSES:
            continue  # roadmap doesn't vouch completion -> leave (deferred etc.)
        if not dry_run:
            text = plan.read_text(encoding="utf-8")
            text = re.sub(r"(?m)^status:\s*.*$",
                          f"status: {satisfied_status}", text, count=1)
            plan.write_text(text, encoding="utf-8")
        try:
            rel = str(plan.relative_to(root))
        except ValueError:
            rel = str(plan)
        changed.append((tid, status or "unknown", rel))
    return changed


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
# Remote-aware preflight (T-044): branch-as-claim across machines.
# The local lease lives under .git/ and is never pushed, so it cannot see a
# teammate's clone. The cross-machine-visible claim signal lanes already
# produce is the branch name (fix/T-NNN-*). This reads the remote for one and
# refuses early — ADVISORY / fail-open: any remote error exits OK, because the
# local lease is the hard gate and offline work must never be blocked.
# --------------------------------------------------------------------------
def task_branch_match(task_id: str, branch: str) -> bool:
    """True if ``branch`` encodes ``task_id`` as a delimited token.

    ``feature/T-044-x``, ``T-044``, ``bugfix/T-044`` match; ``T-44`` /
    ``T-0440`` / ``xT-044`` do not (the id must be bounded by start/end or a
    non-alphanumeric on each side, so a numeric prefix/suffix can't sneak in).
    """
    return re.search(rf"(?<![0-9A-Za-z]){re.escape(task_id)}(?![0-9A-Za-z])",
                     branch) is not None


def remote_task_branches(task_id, remote, root, do_fetch):
    """Return (branches, error). branches: remote branch short-names matching
    the task token. error: a string when the remote could not be consulted
    (caller treats it as fail-open), else None.
    """
    # ls-remote needs no local refs and no working fetch; an optional shallow
    # fetch only refreshes remote-tracking refs for callers that want it.
    if do_fetch:
        _git(["fetch", "--quiet", remote], cwd=str(root))
    have_remote = _git(["remote"], cwd=str(root))
    if not remote_in(remote, have_remote):
        return [], f"no remote named '{remote}'"
    out = _git(["ls-remote", "--heads", remote], cwd=str(root))
    if not out:
        # Empty can mean "no branches" OR an unreachable remote; ls-remote
        # prints nothing and fails silently via _git. Distinguish with a probe.
        probe = subprocess.run(["git", "ls-remote", "--heads", remote],
                               cwd=str(root), capture_output=True, text=True)
        if probe.returncode != 0:
            return [], f"remote '{remote}' unreachable"
        return [], None
    matches = []
    for line in out.splitlines():
        # "<sha>\trefs/heads/<branch>"
        parts = line.split("\trefs/heads/", 1)
        if len(parts) != 2:
            continue
        branch = parts[1].strip()
        if task_branch_match(task_id, branch):
            matches.append(branch)
    return matches, None


def remote_in(name, remote_list):
    return name in {r.strip() for r in remote_list.splitlines() if r.strip()}


# --------------------------------------------------------------------------
# Git-ref distributed locking helpers
# --------------------------------------------------------------------------
def _has_remote(remote: str, root) -> bool:
    """True iff a remote with that name is configured in the repo."""
    listing = _git(["remote"], cwd=str(root))
    return remote_in(remote, listing)


def _push_claim_ref(task_id: str, payload_json: str, root,
                    remote: str = "origin"):
    """Write a git blob, create local ref, push to remote atomically.

    Returns:
      (True,  None)          — pushed successfully (we own the ref)
      (False, existing_json) — ref already existed on remote (another owner)
      (False, None)          — network/git error (fail-open: treat as no remote)
    """
    # Write blob into object store
    blob_result = subprocess.run(
        ["git", "hash-object", "--stdin", "-w"],
        input=payload_json, cwd=str(root),
        capture_output=True, text=True,
    )
    if blob_result.returncode != 0:
        return False, None
    blob_sha = blob_result.stdout.strip()
    if not blob_sha:
        return False, None

    ref = f"refs/openup/claims/{task_id}"

    # Point local ref at blob
    subprocess.run(
        ["git", "update-ref", ref, blob_sha],
        cwd=str(root), capture_output=True,
    )

    # Push without --force: the push is rejected if the ref already exists on
    # the remote (another session owns this task).
    push_result = subprocess.run(
        ["git", "push", remote, f"{ref}:{ref}"],
        cwd=str(root), capture_output=True, text=True,
    )
    if push_result.returncode == 0:
        return True, None

    combined = push_result.stderr + push_result.stdout
    if any(kw in combined for kw in ("rejected", "already exists", "[rejected]",
                                     "already up to date")):
        # Fetch the winning blob so we can report who owns it.
        subprocess.run(
            ["git", "fetch", remote, f"{ref}:{ref}"],
            cwd=str(root), capture_output=True,
        )
        cat_result = subprocess.run(
            ["git", "cat-file", "-p", ref],
            cwd=str(root), capture_output=True, text=True,
        )
        existing_json = cat_result.stdout.strip() if cat_result.returncode == 0 else None
        return False, existing_json

    # Any other error (network, auth, etc.) → fail-open
    return False, None


def _fetch_remote_claims(root, cdir, remote: str = "origin"):
    """Fetch refs/openup/claims/* from origin and mirror them to local files.

    Returns an error string on failure, None on success.  Fail-open: callers
    ignore the return value and continue with whatever local files exist.
    """
    result = subprocess.run(
        ["git", "fetch", remote,
         "+refs/openup/claims/*:refs/openup/claims/*"],
        cwd=str(root), capture_output=True, text=True,
    )
    if result.returncode != 0:
        return f"fetch failed: {result.stderr.strip()}"
    _sync_refs_to_local(root, cdir)
    return None


def _sync_refs_to_local(root, cdir: Path):
    """Read all refs/openup/claims/* refs and write them as local JSON files.

    Creates cdir if needed.  Only updates a file when its content differs
    from the existing file (avoids spurious mtime changes).
    """
    ls_result = subprocess.run(
        ["git", "for-each-ref", "--format=%(refname) %(objectname)",
         "refs/openup/claims/"],
        cwd=str(root), capture_output=True, text=True,
    )
    if ls_result.returncode != 0 or not ls_result.stdout.strip():
        return

    cdir.mkdir(parents=True, exist_ok=True)
    for line in ls_result.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) != 2:
            continue
        refname, sha = parts
        # refname = refs/openup/claims/<task-id>
        task_id = refname.split("/")[-1]
        if not task_id:
            continue
        cat_result = subprocess.run(
            ["git", "cat-file", "-p", sha],
            cwd=str(root), capture_output=True, text=True,
        )
        if cat_result.returncode != 0:
            continue
        content = cat_result.stdout
        fp = cdir / f"{task_id}.json"
        existing = fp.read_text(encoding="utf-8") if fp.exists() else None
        if content != existing:
            fp.write_text(content, encoding="utf-8")


def _delete_claim_ref(task_id: str, root, remote: str = "origin"):
    """Delete the remote and local claim refs (idempotent, fail-open)."""
    ref = f"refs/openup/claims/{task_id}"
    # Delete remote ref (push refspec :<ref> = delete)
    subprocess.run(
        ["git", "push", remote, f":{ref}"],
        cwd=str(root), capture_output=True,
    )
    # Delete local ref
    subprocess.run(
        ["git", "update-ref", "-d", ref],
        cwd=str(root), capture_output=True,
    )


def remote_check(task_id, remote, root, do_fetch, self_branch):
    """Return (exit_code, message). EXIT_REMOTE_DUP only when a remote branch
    *other than* our own (self_branch) encodes the task. Fail-open otherwise.
    """
    branches, error = remote_task_branches(task_id, remote, root, do_fetch)
    if error is not None:
        return EXIT_OK, f"SKIP (advisory): {error} — remote not consulted"
    others = [b for b in branches if b != self_branch]
    if others:
        owners = ", ".join(sorted(others))
        return EXIT_REMOTE_DUP, (
            f"REMOTE DUPLICATE: task {task_id} already has branch(es) "
            f"[{owners}] on '{remote}'. Another clone is (or was) on this task. "
            f"Pick a different lane, or coordinate before continuing."
        )
    return EXIT_OK, f"READY: no remote branch for {task_id} on '{remote}'"


# --------------------------------------------------------------------------
# Subcommands
# --------------------------------------------------------------------------
def cmd_dir(args):
    print(claims_dir(override=args.claims_dir))
    return EXIT_OK


def cmd_preflight(args):
    root = (Path(args.repo_root).resolve()
            if getattr(args, "repo_root", None) else repo_root())
    cdir = claims_dir(override=args.claims_dir)
    # Fetch remote claims so local files reflect the distributed state.
    # Fail-open: skip when --no-push is set or no remote is configured.
    no_push = getattr(args, "no_push", False)
    remote = getattr(args, "remote", "origin")
    if not no_push and _has_remote(remote, root):
        _fetch_remote_claims(root, cdir, remote)
    touches, deps = resolve_task_inputs(args, root)
    code, msg = preflight(args.task_id, touches, deps, cdir, root)
    (print if code == EXIT_OK else lambda m: sys.stderr.write(m + "\n"))(msg)
    return code


def cmd_migrate_archived_status(args):
    root = (Path(args.repo_root).resolve()
            if getattr(args, "repo_root", None) else repo_root())
    changed = migrate_archived_status(
        root, satisfied_status=args.satisfied_status, dry_run=args.dry_run)
    verb = "would bump" if args.dry_run else "bumped"
    if not changed:
        print("no stale archived plans (idempotent: nothing to change)")
        return EXIT_OK
    for tid, old, rel in changed:
        print(f"{verb} {tid}: status '{old}' -> '{args.satisfied_status}'  ({rel})")
    print(f"{verb} {len(changed)} archived plan(s)")
    return EXIT_OK


def cmd_remote_check(args):
    root = repo_root()
    self_branch = args.self_branch
    if self_branch is None:
        self_branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=str(root))
    code, msg = remote_check(
        args.task_id, args.remote, root,
        do_fetch=not args.no_fetch, self_branch=self_branch,
    )
    (print if code == EXIT_OK else lambda m: sys.stderr.write(m + "\n"))(msg)
    return code


def cmd_claim(args):
    root = repo_root()
    cdir = claims_dir(override=args.claims_dir)
    no_push = getattr(args, "no_push", False)
    remote = getattr(args, "remote", "origin")
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
    fp = claim_file(args.task_id, cdir)
    write_claim_atomic(fp, payload)

    # Distributed locking: push the claim ref to origin so other machines see it.
    # Skip when --no-push is set (test mode) or no remote is configured.
    if not no_push and _has_remote(remote, root):
        import io as _io
        payload_json = _io.StringIO()
        json.dump(payload, payload_json, indent=2)
        payload_json.write("\n")
        ok, existing_json = _push_claim_ref(
            args.task_id, payload_json.getvalue(), root, remote
        )
        if not ok:
            if existing_json is not None:
                # Another session on a different machine already owns this task.
                try:
                    existing_data = json.loads(existing_json)
                    owner_sess = existing_data.get("session_id") or "unknown-session"
                    owner_branch = existing_data.get("branch") or "unknown-branch"
                except (json.JSONDecodeError, ValueError):
                    owner_sess = "unknown-session"
                    owner_branch = "unknown-branch"
                # Roll back local claim file — we lost the race.
                fp.unlink(missing_ok=True)
                sys.stderr.write(
                    f"REFUSED: {args.task_id} already claimed on remote by session "
                    f"{owner_sess} (branch {owner_branch}). "
                    f"Coordinate before continuing.\n"
                )
                return EXIT_OTHER_OWNER
            else:
                # Network error — keep local claim and continue (fail-open).
                sys.stderr.write(
                    f"WARNING: could not push claim ref for {args.task_id} to "
                    f"'{remote}' (network error). Proceeding with local-only claim "
                    f"(same behaviour as before git-ref locking).\n"
                )

    print(f"Claimed {args.task_id} -> {fp}")
    return EXIT_OK


def cmd_release(args):
    cdir = claims_dir(override=args.claims_dir)
    fp = claim_file(args.task_id, cdir)
    if fp.exists():
        fp.unlink()
        print(f"Released {args.task_id}")
    else:
        print(f"No claim for {args.task_id} (already released)")  # idempotent

    # Delete remote claim ref (fail-open, idempotent).
    no_push = getattr(args, "no_push", False)
    remote = getattr(args, "remote", "origin")
    if not no_push:
        root = repo_root()
        if _has_remote(remote, root):
            _delete_claim_ref(args.task_id, root, remote)

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

    def add_push_flags(sp):
        """Add --no-push and --remote flags for distributed-lock control."""
        sp.add_argument(
            "--no-push", action="store_true",
            help="Skip all network/git-ref operations (local-only mode; used by tests).",
        )
        sp.add_argument(
            "--remote", default="origin",
            help="Remote name for git-ref claim operations (default: origin).",
        )

    p_pf = sub.add_parser("preflight", help="Check deps + collision; write nothing.")
    p_pf.add_argument("--task-id", required=True)
    p_pf.add_argument(
        "--repo-root", default=None,
        help="Override the repo root scanned for deps/roadmap (tests).",
    )
    add_task_inputs(p_pf)
    add_common(p_pf)
    add_push_flags(p_pf)
    p_pf.set_defaults(func=cmd_preflight)

    p_mas = sub.add_parser(
        "migrate-archived-status",
        help="Repair archived plans whose body status is stale (non-satisfied) "
             "but whose roadmap row is completed; bump them to a satisfied "
             "status. Idempotent; leaves deferred/cancelled plans untouched.",
    )
    p_mas.add_argument(
        "--dry-run", action="store_true",
        help="Report what would change without writing.",
    )
    p_mas.add_argument(
        "--satisfied-status", default="done",
        help="Status to write into stale archived plans (default: done).",
    )
    p_mas.add_argument(
        "--repo-root", default=None,
        help="Override the repo root scanned (tests).",
    )
    p_mas.set_defaults(func=cmd_migrate_archived_status)

    p_rc = sub.add_parser(
        "remote-check",
        help="Advisory cross-machine check: refuse (exit 9) if a remote branch "
             "already encodes the task. Fail-open on any remote error.",
    )
    p_rc.add_argument("--task-id", required=True)
    p_rc.add_argument("--remote", default="origin", help="Remote name (default: origin).")
    p_rc.add_argument(
        "--no-fetch", action="store_true",
        help="Use existing remote-tracking refs; skip the network fetch.",
    )
    p_rc.add_argument(
        "--self-branch", default=None,
        help="Our own lane branch to exclude from matches (default: current HEAD).",
    )
    p_rc.add_argument(
        "--no-push", action="store_true",
        help="Skip all network/git-ref operations (local-only mode; used by tests).",
    )
    p_rc.set_defaults(func=cmd_remote_check)

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
    add_push_flags(p_cl)
    p_cl.set_defaults(func=cmd_claim)

    p_rl = sub.add_parser("release", help="Delete a task's claim (idempotent).")
    p_rl.add_argument("--task-id", required=True)
    add_common(p_rl)
    add_push_flags(p_rl)
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
