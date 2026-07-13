#!/usr/bin/env python3
"""OpenUP roadmap interface (T-064).

Gives ``docs/roadmap.md`` a machine-readable query surface so the ONE remaining
model-executed step in the ``/openup-next`` pipeline — promote-step task
selection (§1c) — becomes deterministic. Two sessions on identical inputs pick
the same task, and neither reads the whole roadmap into context.

Subcommands:
  list [--status pending|planned|completed|all]
            JSON array of matching entries in roadmap **document order**
            (default = pending + planned). The order IS the product-manager's
            given value order — this script consumes it, never re-ranks.
  get T-NNN JSON for one entry (exit 3 if absent).
  next      The first promotable pending/planned entry (document order) whose
            deps are all satisfied, with no change folder (active OR archived —
            the P2 re-promotion guard), no live lease, and — unless
            ``--no-remote-check`` — no branch encoding its id on ``origin`` (the
            T-066 delivered-but-unmerged guard: a task finished in an open PR is
            invisible to the local guards, so it would otherwise be re-promoted).
            Exit 3 + a specific stderr reason when nothing is promotable,
            mirroring ``openup-board.py top``. Fail-open: any remote error leaves
            promotion exactly as it was without the guard.

Determinism: no wall-clock, no randomness — identical roadmap + claims/folders
→ byte-identical ``next`` output. Read-only: writes nothing.

Design rules (mirror scripts/openup-board.py):
  * Python standard library only; never invokes a model.
  * Lease/repo-root resolution is *imported* from openup-claims.py, not
    re-implemented, so "no live lease" here means the same thing the claim
    machinery means.

Exit codes:
  0  success
  2  argparse / usage error
  3  next: nothing promotable (reason on stderr) · get: id not found
"""

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

# Reuse openup-claims.py (hyphenated filename → importlib), same as the board.
_CLAIMS_PATH = Path(__file__).resolve().parent / "openup-claims.py"
_spec = importlib.util.spec_from_file_location("openup_claims", _CLAIMS_PATH)
claims = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(claims)  # type: ignore[union-attr]

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NONE = 3

# A task is "effectively completed" (delivered) when its status word is one of
# these — OR when an archived change folder exists (true-delivery evidence that
# survives the manual-section status-rot; see spec Assumption + exploration P2).
DONE_STATUSES = {"completed", "done", "verified"}
# Statuses that make a task a promote candidate.
PROMOTABLE_STATUSES = {"pending", "planned"}

ID_RE = re.compile(r"T-\d+")
SECTION_RE = re.compile(r"^##\s+(T-\d+)\s*:\s*(.*)$")
FIELD_RE = re.compile(r"^\*\*(?P<key>[^*]+)\*\*\s*:\s*(?P<val>.*)$")


# --------------------------------------------------------------------------
# Parsing — both roadmap entry shapes, in document order
# --------------------------------------------------------------------------
def _status_word(raw: str) -> str:
    """First bare word of a status cell: ``completed (2026-07-05)`` → ``completed``."""
    raw = raw.strip().strip("`").lower()
    m = re.match(r"[a-z]+", raw)
    return m.group(0) if m else raw


def _parse_depends(raw: str):
    """Extract T-NNN ids from a depends-on cell/field (``—`` / ``none`` → [])."""
    return ID_RE.findall(raw or "")


def _split_row(line: str):
    """Split a markdown table row into trimmed cells (drop the outer empties)."""
    parts = [c.strip() for c in line.strip().strip("|").split("|")]
    return parts


def _is_separator(cells):
    return all(set(c) <= set("-: ") and c for c in cells) if cells else False


def _header_map(cells):
    """Map a table header row to {logical_field: column_index}, or None if this
    is not a task table (no ID column)."""
    idx = {}
    for i, c in enumerate(cells):
        key = c.strip().lower()
        if key == "id":
            idx["id"] = i
        elif key == "title":
            idx["title"] = i
        elif key == "status":
            idx["status"] = i
        elif key == "priority":
            idx["priority"] = i
        elif key.startswith("depends"):
            idx["depends_on"] = i
    return idx if "id" in idx and "status" in idx else None


def _entry(id_, title, status, priority, depends_on, value, see):
    return {
        "id": id_,
        "title": (title or "").strip() or None,
        "status": status,
        "priority": (priority or "").strip().lower() or None,
        "depends_on": depends_on,
        "value": (value or "").strip() or None,
        "see": (see or "").strip().strip("`") or None,
    }


def _parse_section(lines, start, task_id, title):
    """Parse a manual ``## T-NNN:`` section starting at index ``start``.
    Returns (entry, next_index)."""
    fields = {}
    i = start + 1
    while i < len(lines):
        line = lines[i]
        if line.startswith("## ") or line.startswith("### ") or line.startswith("# "):
            break
        m = FIELD_RE.match(line.strip())
        if m:
            fields[m.group("key").strip().lower()] = m.group("val").strip()
        i += 1
    entry = _entry(
        task_id,
        title,
        _status_word(fields.get("status", "")),
        fields.get("priority"),
        _parse_depends(fields.get("dependencies", "")),
        fields.get("value"),
        fields.get("see"),
    )
    return entry, i


def parse_roadmap(text: str):
    """Return every T-NNN roadmap entry (table rows + ``## T-NNN:`` sections) in
    document order. Program-level ``### Planned:`` blocks (no T-NNN in their
    heading) are not tasks and are skipped."""
    entries = []
    seen = set()
    lines = text.splitlines()
    header = None
    i = 0
    while i < len(lines):
        line = lines[i]
        sm = SECTION_RE.match(line)
        if sm:
            entry, i = _parse_section(lines, i, sm.group(1), sm.group(2))
            if entry["id"] not in seen:
                entries.append(entry)
                seen.add(entry["id"])
            header = None
            continue
        if line.lstrip().startswith("|"):
            cells = _split_row(line)
            if _is_separator(cells):
                i += 1
                continue
            hm = _header_map(cells)
            if hm is not None:
                header = hm
                i += 1
                continue
            if header is not None:
                idcell = cells[header["id"]] if header["id"] < len(cells) else ""
                idm = ID_RE.search(idcell)
                if idm and idm.group(0) not in seen:
                    dep_i = header.get("depends_on")
                    pri_i = header.get("priority")
                    ti_i = header.get("title")
                    entries.append(_entry(
                        idm.group(0),
                        cells[ti_i] if ti_i is not None and ti_i < len(cells) else "",
                        _status_word(cells[header["status"]]),
                        cells[pri_i] if pri_i is not None and pri_i < len(cells) else "",
                        _parse_depends(cells[dep_i]) if dep_i is not None and dep_i < len(cells) else [],
                        None,
                        None,
                    ))
                    seen.add(idm.group(0))
            i += 1
            continue
        # Any non-table line ends the current table's column context.
        header = None
        i += 1
    return entries


# --------------------------------------------------------------------------
# Delivery evidence (status-rot resistant)
# --------------------------------------------------------------------------
def _active_folder(root: Path, task_id: str) -> bool:
    return (root / "docs" / "changes" / task_id / "plan.md").exists()


def _archived_folder(root: Path, task_id: str) -> bool:
    return (root / "docs" / "changes" / "archive" / task_id).is_dir()


def _effectively_completed(root: Path, entry: dict) -> bool:
    """Delivered per true evidence: a done status word OR an archived folder
    (guards against a stale-``pending`` manual section — exploration P2)."""
    return entry["status"] in DONE_STATUSES or _archived_folder(root, entry["id"])


# --------------------------------------------------------------------------
# Subcommands
# --------------------------------------------------------------------------
def _repo_root(args) -> Path:
    return Path(args.root).resolve() if args.root else claims.repo_root()


def _roadmap_text(root: Path) -> str:
    """The roadmap's text, or "" when the file does not exist (T-093).

    A freshly bootstrapped project has no docs/roadmap.md until Inception
    authors it — that is a valid state, not an error: `list` yields [],
    `get`/`next` exit 3, and openup-board.py `resolve` degrades to a clean
    decision instead of a FileNotFoundError traceback.
    """
    try:
        return (root / "docs" / "roadmap.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _status_matches(entry_status: str, want: str) -> bool:
    if want == "all":
        return True
    if want == "completed":
        return entry_status in DONE_STATUSES
    if want is None:  # default: promotable
        return entry_status in PROMOTABLE_STATUSES
    return entry_status == want


def cmd_list(args):
    root = _repo_root(args)
    entries = parse_roadmap(_roadmap_text(root))
    out = [e for e in entries if _status_matches(e["status"], args.status)]
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return EXIT_OK


def cmd_get(args):
    root = _repo_root(args)
    entries = parse_roadmap(_roadmap_text(root))
    for e in entries:
        if e["id"] == args.task_id:
            print(json.dumps(e, indent=2, ensure_ascii=False))
            return EXIT_OK
    sys.stderr.write(f"{args.task_id} not found in docs/roadmap.md\n")
    return EXIT_NONE


def cmd_next(args):
    root = _repo_root(args)
    entries = parse_roadmap(_roadmap_text(root))
    by_id = {e["id"]: e for e in entries}
    cdir = claims.claims_dir(override=args.claims_dir)
    leased = {
        c.get("task_id")
        for c in claims.live_claims(cdir)
        if c.get("task_id") and not c.get("_corrupt")
    }

    # Remote delivered-but-unmerged guard (T-066). A task fully delivered in an
    # open, unmerged PR is invisible to every LOCAL guard above: its change
    # folder was archived on the branch (not here), its lease was released at
    # complete-task, and the roadmap row still reads ``pending`` on trunk. The
    # one cross-machine signal that survives is the branch on ``origin`` — the
    # same branch-as-claim T-044 already reads. We consult it once (cached),
    # fail-open on any remote error so offline / no-remote / non-repo runs are
    # never blocked, and skip a candidate whose id a remote branch encodes.
    remote = getattr(args, "remote", "origin")
    remote_check_on = not getattr(args, "no_remote_check", False)
    _heads_cache = {}  # single-slot cache → ONE ls-remote per invocation (req 3)

    def _remote_head_branches():
        """(branches, error) for all ``origin`` heads — fail-open. Fetched once
        and cached so N candidates cost ONE ls-remote. Mirrors the probe in
        claims.remote_task_branches but returns the *unfiltered* set; the token
        matcher (claims.task_branch_match) is reused per candidate, not copied."""
        if "v" not in _heads_cache:
            if not claims.remote_in(remote, claims._git(["remote"], cwd=str(root))):
                _heads_cache["v"] = ([], f"no remote named '{remote}'")
            else:
                out = claims._git(["ls-remote", "--heads", remote], cwd=str(root))
                if not out:
                    # Empty is ambiguous (no branches vs unreachable) — probe.
                    probe = subprocess.run(
                        ["git", "ls-remote", "--heads", remote],
                        cwd=str(root), capture_output=True, text=True)
                    _heads_cache["v"] = (
                        ([], f"remote '{remote}' unreachable")
                        if probe.returncode != 0 else ([], None))
                else:
                    branches = [
                        p[1].strip()
                        for p in (line.split("\trefs/heads/", 1)
                                  for line in out.splitlines())
                        if len(p) == 2]
                    _heads_cache["v"] = (branches, None)
        return _heads_cache["v"]

    def remote_branch_for(task_id):
        """Matching remote branch name, or None. None also on any remote error
        (fail-open): a delivered-but-unmerged skip requires positive evidence."""
        branches, err = _remote_head_branches()
        if err is not None:
            return None
        for b in branches:
            if claims.task_branch_match(task_id, b):
                return b
        return None

    def deps_ok(entry):
        for dep in entry["depends_on"]:
            dep_entry = by_id.get(dep)
            done = (dep_entry is not None and dep_entry["status"] in DONE_STATUSES) \
                or _archived_folder(root, dep)
            if not done:
                return dep
        return None

    saw_pending = False
    first_blocked = None
    saw_inflight = False
    remote_skipped = None  # (task_id, branch) — sole-blocker delivered-but-unmerged
    for e in entries:
        if e["status"] not in PROMOTABLE_STATUSES:
            continue
        if _effectively_completed(root, e):
            continue  # stale-``pending`` but actually delivered — never re-promote
        saw_pending = True
        if _active_folder(root, e["id"]) or e["id"] in leased:
            saw_inflight = True
            continue  # already a lane / in flight elsewhere
        blocked_on = deps_ok(e)
        if blocked_on is not None:
            if first_blocked is None:
                first_blocked = (e["id"], blocked_on)
            continue
        if remote_check_on:
            rbranch = remote_branch_for(e["id"])
            if rbranch is not None:
                # Delivered-but-unmerged: an origin branch encodes this id (an
                # open PR). Skip like any in-flight lane — never re-promote it.
                saw_inflight = True
                if remote_skipped is None:
                    remote_skipped = (e["id"], rbranch)
                continue
        print(json.dumps(e, indent=2, ensure_ascii=False))
        return EXIT_OK

    if not saw_pending:
        reason = "roadmap exhausted — no promotable pending task."
    elif first_blocked is not None:
        reason = f"next pending {first_blocked[0]} blocked on {first_blocked[1]}."
    elif remote_skipped is not None:
        reason = (f"{remote_skipped[0]} delivered-but-unmerged — origin branch "
                  f"'{remote_skipped[1]}' exists; merge its PR instead of "
                  f"re-promoting.")
    elif saw_inflight:
        reason = "all pending tasks in flight (change folder or live lease present)."
    else:
        reason = "roadmap exhausted — no promotable pending task."
    sys.stderr.write(reason + "\n")
    return EXIT_NONE


def main(argv=None):
    parser = argparse.ArgumentParser(prog="openup-roadmap.py", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--root", help="Repo root override (default: git toplevel).")
        sp.add_argument("--claims-dir", help="Override the leases dir (tests).")

    p_list = sub.add_parser("list", help="List roadmap entries (document order).")
    p_list.add_argument(
        "--status",
        choices=["pending", "planned", "completed", "all"],
        default=None,
        help="Filter by status (default: pending + planned).",
    )
    common(p_list)
    p_list.set_defaults(func=cmd_list)

    p_get = sub.add_parser("get", help="Get one roadmap entry by id.")
    p_get.add_argument("task_id")
    common(p_get)
    p_get.set_defaults(func=cmd_get)

    p_next = sub.add_parser("next", help="Print the next promotable task (exit 3 if none).")
    common(p_next)
    p_next.add_argument(
        "--remote", default="origin",
        help="Remote consulted for delivered-but-unmerged branches (default: origin).")
    p_next.add_argument(
        "--no-remote-check", action="store_true",
        help="Disable the remote delivered-but-unmerged guard (offline/hermetic).")
    p_next.set_defaults(func=cmd_next)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
