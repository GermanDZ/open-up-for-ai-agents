#!/usr/bin/env python3
"""sync-status.py — single-source roadmap / project-status generator.

Reads ``.openup/state.json`` and ``docs/roadmap.md`` and makes the two human
views agree with machine state:

  1. Flips the current task's ``Status`` cell in the roadmap task table to
     match state (derived: ``completed`` when the track's required gates are
     all met, otherwise ``in-progress``).
  2. Regenerates the header fields of ``docs/project-status.md`` (Iteration,
     Current Task, Status, Iteration Goal, Last Updated, Phase) from state +
     roadmap so the two documents can never disagree.
  3. Regenerates the ``## Notes`` section of ``docs/project-status.md`` from
     the sharded note files in ``docs/status-notes/`` (T-024): one file per
     completion, newest-first by filename. Lanes write their own note file
     (conflict-free by construction) instead of prepending to the shared doc;
     this script derives the view. Skipped when the directory is absent or
     empty, so repos without sharded notes keep their hand-written section.

On success, sets ``gates.roadmap_synced true`` via openup-state.py.

Because every field this script writes is derived, the resolution for a merge
conflict in either view is never a hand-merge: rebase onto the trunk and
re-run this script.

Design rules (match openup-state.py):
  * Deterministic, Python standard library only.
  * Idempotent: re-running with unchanged state produces no further changes.
  * ``--state-dir`` overrides the ``.openup`` directory (tests use this).

Exit codes:
  0  success
  3  no state file present
  4  roadmap / project-status file missing
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

EXIT_OK = 0
EXIT_NO_STATE = 3
EXIT_NO_DOC = 4

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
STATE_CLI = SCRIPT_DIR / "openup-state.py"

# Track → required gates (mirrors openup-state.py DEFAULT_REQUIRED_GATES and
# the quick-track relaxation documented in docs-eng-process/state-file.md).
# Track-required gates for the derived "completed" status. Mirrors
# /openup-complete-task's check-gates and the solo-by-default model: only `full`
# requires a team. `standard` is solo unless a team is explicitly opted in, so
# requiring team_deployed here would leave every solo standard task permanently
# "in-progress" (T-041 F11).
TRACK_REQUIRED = {
    "quick": ["log_written", "roadmap_synced"],
    "standard": ["log_written", "roadmap_synced"],
    "full": ["team_deployed", "log_written", "roadmap_synced"],
}


def state_dir(args) -> Path:
    if getattr(args, "state_dir", None):
        return Path(args.state_dir).expanduser().resolve()
    return REPO_ROOT / ".openup"


def roadmap_path(args) -> Path:
    if getattr(args, "roadmap", None):
        return Path(args.roadmap).expanduser().resolve()
    return REPO_ROOT / "docs" / "roadmap.md"


def project_status_path(args) -> Path:
    if getattr(args, "project_status", None):
        return Path(args.project_status).expanduser().resolve()
    return REPO_ROOT / "docs" / "project-status.md"


def notes_dir(args) -> Path:
    if getattr(args, "notes_dir", None):
        return Path(args.notes_dir).expanduser().resolve()
    return REPO_ROOT / "docs" / "status-notes"


def read_state(args):
    p = state_dir(args) / "state.json"
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def derive_status(state: dict) -> str:
    """completed when all track-required gates are truthy, else in-progress."""
    track = state.get("track", "standard")
    required = TRACK_REQUIRED.get(track, TRACK_REQUIRED["standard"])
    gates = state.get("gates", {})
    if all(gates.get(g) for g in required):
        return "completed"
    return "in-progress"


# --------------------------------------------------------------------------
# Roadmap table editing
# --------------------------------------------------------------------------
def _id_cell_matches(cell: str, task_id: str) -> bool:
    """The ID cell may be bare (``T-024``) or a markdown link
    (``[T-024](changes/archive/T-024/plan.md)``) — match both."""
    cell = cell.strip()
    if cell == task_id:
        return True
    if cell.startswith("[") and "](" in cell:
        return cell[1:cell.index("](")].strip() == task_id
    return False


def update_roadmap(text: str, task_id: str, status: str,
                   today: str) -> tuple[str, str | None]:
    """Flip the Status cell for ``task_id`` in the first matching table row.

    A ``completed`` status is stamped ``completed (YYYY-MM-DD)`` to match the
    roadmap's hand-written convention; the stamp is idempotent (re-running on
    an already-stamped cell keeps its original date).

    Returns (new_text, title) where title is the task's Title column value
    (used to seed the project-status Iteration Goal), or None if not found.
    """
    lines = text.splitlines(keepends=True)
    title = None
    row_re = re.compile(r"^\s*\|")
    for i, line in enumerate(lines):
        if not row_re.match(line):
            continue
        cells = line.split("|")
        # A table row split on '|' has a leading and trailing empty cell.
        if len(cells) < 4:
            continue
        if _id_cell_matches(cells[1], task_id):
            title = cells[2].strip() if len(cells) > 2 else None
            cell = status
            if status == "completed":
                current = cells[3].strip()
                if current.startswith("completed ("):
                    cell = current  # keep the original completion date
                else:
                    cell = f"completed ({today})"
            cells[3] = f" {cell} "
            lines[i] = "|".join(cells)
            return "".join(lines), title

    # No table row matched — fall back to the free-form ``## <task_id>:`` section
    # emitted by /openup-plan-feature, whose status lives in a ``**Status**:``
    # line, not a table cell. Without this fallback those sections rot (they are
    # updated only by hand — the exact bug T-067 fixes).
    new_text, _, sec_title = stamp_section_status(text, task_id, status, today)
    return new_text, sec_title


# --------------------------------------------------------------------------
# Free-form ``## T-NNN:`` section Status lines (T-067)
# --------------------------------------------------------------------------
_SECTION_STATUS_RE = re.compile(r"^\*\*Status\*\*:\s*(.*?)\s*$")


def _section_bounds(lines: list[str], task_id: str) -> tuple[int, int] | None:
    """Return (header_idx, end_idx) for the ``## <task_id>:`` section, where
    end_idx is the line of the next ``## `` header (or len(lines)). None if the
    section is absent."""
    header_re = re.compile(rf"^##\s+{re.escape(task_id)}:")
    start = None
    for i, line in enumerate(lines):
        if start is None:
            if header_re.match(line):
                start = i
            continue
        if line.startswith("## "):
            return start, i
    if start is not None:
        return start, len(lines)
    return None


def find_section_status(text: str, task_id: str) -> tuple[int, str] | None:
    """Locate the ``**Status**:`` line inside the ``## <task_id>:`` section.
    Returns (line_index, current_value) or None if section/line is absent."""
    lines = text.splitlines(keepends=True)
    bounds = _section_bounds(lines, task_id)
    if bounds is None:
        return None
    start, end = bounds
    for i in range(start + 1, end):
        m = _SECTION_STATUS_RE.match(lines[i].rstrip("\n"))
        if m:
            return i, m.group(1).strip()
    return None


def _section_title(text: str, task_id: str) -> str | None:
    """The prose title after ``## <task_id>:`` (used to seed the goal), if any."""
    m = re.search(rf"^##\s+{re.escape(task_id)}:\s*(.*?)\s*$", text, re.MULTILINE)
    return m.group(1).strip() if m and m.group(1).strip() else None


def stamp_section_status(text: str, task_id: str, status: str,
                         today: str) -> tuple[str, bool, str | None]:
    """Stamp the ``**Status**:`` line of the ``## <task_id>:`` section.

    Mirrors the table-cell convention: a ``completed`` status is stamped
    ``completed (YYYY-MM-DD)`` and is idempotent (an existing completion date is
    preserved). Returns (new_text, changed, section_title).
    """
    found = find_section_status(text, task_id)
    title = _section_title(text, task_id)
    if found is None:
        return text, False, title
    idx, current = found
    new_value = status
    if status == "completed":
        new_value = current if current.startswith("completed (") else f"completed ({today})"
    if new_value == current:
        return text, False, title
    lines = text.splitlines(keepends=True)
    eol = "\n" if lines[idx].endswith("\n") else ""
    lines[idx] = f"**Status**: {new_value}{eol}"
    return "".join(lines), True, title


# --------------------------------------------------------------------------
# --reconcile sweep — self-heal section statuses from archived-folder truth
# --------------------------------------------------------------------------
def archived_task_ids(root: Path) -> list[str]:
    """Task IDs with an archived change folder under docs/changes/archive/."""
    adir = root / "docs" / "changes" / "archive"
    if not adir.is_dir():
        return []
    id_re = re.compile(r"^T-\d+$")
    return sorted(p.name for p in adir.iterdir() if p.is_dir() and id_re.match(p.name))


def archival_date(task_id: str, root: Path, today: str) -> str:
    """Date the change folder was archived (last commit touching it), YYYY-MM-DD.
    Falls back to ``today`` when git is unavailable or the path has no history."""
    rel = f"docs/changes/archive/{task_id}"
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", rel],
            cwd=str(root), capture_output=True, text=True,
        )
        date = out.stdout.strip()
        if out.returncode == 0 and re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            return date
    except (OSError, ValueError):
        pass
    return today


def section_status_drift(text: str, root: Path) -> list[tuple[str, str]]:
    """(task_id, current_status) for every ``## T-NNN:`` section whose change
    folder is archived but whose Status is not yet ``completed``. This is the
    single source of truth for both --reconcile and openup-doctor's read-only
    drift check (T-067)."""
    drift = []
    for task_id in archived_task_ids(root):
        found = find_section_status(text, task_id)
        if found is None:
            continue
        _, current = found
        if not current.startswith("completed"):
            drift.append((task_id, current))
    return drift


def reconcile_sections(text: str, root: Path,
                       today: str) -> tuple[str, list[tuple[str, str]]]:
    """Stamp ``completed (<archival-date>)`` on every drifted section. Returns
    (new_text, [(task_id, stamped_date), …]). Idempotent."""
    changed = []
    for task_id, _current in section_status_drift(text, root):
        date = archival_date(task_id, root, today)
        new_text, did, _ = stamp_section_status(text, task_id, "completed", date)
        if did:
            text = new_text
            changed.append((task_id, date))
    return text, changed


# --------------------------------------------------------------------------
# project-status.md regeneration
# --------------------------------------------------------------------------
def set_field(text: str, field: str, value: str) -> str:
    """Replace a **Field**: value line, preserving the rest of the doc."""
    pat = re.compile(rf"^\*\*{re.escape(field)}\*\*:.*$", re.MULTILINE)
    repl = f"**{field}**: {value}"
    if pat.search(text):
        return pat.sub(lambda _m: repl, text, count=1)
    return text


def update_project_status(text: str, state: dict, status: str,
                          goal: str | None, today: str) -> str:
    text = set_field(text, "Phase", state.get("phase", ""))
    text = set_field(text, "Iteration", str(state.get("iteration", "")))
    text = set_field(text, "Current Task", state.get("task_id", ""))
    text = set_field(text, "Status", status)
    if goal:
        text = set_field(text, "Iteration Goal", goal)
    text = set_field(text, "Last Updated", today)
    text = set_field(text, "Updated By", "sync-status.py")
    return text


# --------------------------------------------------------------------------
# Sharded status notes -> ## Notes section (T-024)
# --------------------------------------------------------------------------
def assemble_notes(ndir: Path) -> str | None:
    """Concatenate docs/status-notes/*.md newest-first (filename descending —
    files are date-prefixed). None when the directory is absent/empty."""
    if not ndir.is_dir():
        return None
    chunks = []
    for fp in sorted(ndir.glob("*.md"), key=lambda p: p.name, reverse=True):
        body = fp.read_text(encoding="utf-8").strip()
        if body:
            chunks.append(body)
    if not chunks:
        return None
    return "\n\n".join(chunks) + "\n"


def update_notes_section(text: str, notes_block: str) -> str:
    """Replace the body of ``## Notes`` (up to the next ``## `` heading or
    EOF) with the assembled block; append the section if it is missing."""
    lines = text.splitlines(keepends=True)
    start = None
    for i, line in enumerate(lines):
        if line.rstrip("\n").strip() == "## Notes":
            start = i
            break
    if start is None:
        if not text.endswith("\n"):
            text += "\n"
        return text + "\n## Notes\n\n" + notes_block
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    head = "".join(lines[: start + 1])
    tail = "".join(lines[end:])
    return head + "\n" + notes_block + ("\n" if tail else "") + tail


def set_gate_roadmap_synced(args) -> None:
    cmd = [sys.executable, str(STATE_CLI), "set-gate", "roadmap_synced", "true"]
    if getattr(args, "state_dir", None):
        cmd += ["--state-dir", str(state_dir(args))]
    subprocess.run(cmd, capture_output=True, text=True)


def run_reconcile(args) -> int:
    """--reconcile entrypoint. State-free: derives completion purely from the
    archived change folders, so it heals rot regardless of iteration state.
    ``--dry-run`` reports drift without writing (read-only; used by
    openup-doctor). Machine-readable ``DRIFT <id> <status>`` lines let callers
    parse the set."""
    rm_path = roadmap_path(args)
    if not rm_path.exists():
        sys.stderr.write(f"Missing doc: roadmap={rm_path}\n")
        return EXIT_NO_DOC
    root = rm_path.resolve().parent.parent  # docs/roadmap.md -> repo root
    text = rm_path.read_text(encoding="utf-8")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if args.dry_run:
        drift = section_status_drift(text, root)
        for task_id, current in drift:
            print(f"DRIFT {task_id} {current}")
        print(f"drift: {len(drift)} section(s)")
        return EXIT_OK

    new_text, changed = reconcile_sections(text, root, today)
    if new_text != text:
        rm_path.write_text(new_text, encoding="utf-8")
    if changed:
        summary = ", ".join(f"{t} ({d})" for t, d in changed)
        print(f"reconciled {len(changed)} section(s): {summary}")
    else:
        print("reconciled 0 section(s).")
    return EXIT_OK


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="sync-status.py",
        description="Sync roadmap + project-status.md from .openup/state.json.",
    )
    parser.add_argument("--state-dir", help="Override the .openup directory.")
    parser.add_argument("--roadmap", help="Override docs/roadmap.md path.")
    parser.add_argument(
        "--project-status", help="Override docs/project-status.md path."
    )
    parser.add_argument(
        "--notes-dir", help="Override docs/status-notes/ path."
    )
    parser.add_argument(
        "--no-gate",
        action="store_true",
        help="Skip setting gates.roadmap_synced (used in isolated tests).",
    )
    parser.add_argument(
        "--reconcile",
        action="store_true",
        help="Self-heal: stamp completed(<archival-date>) on every free-form "
             "'## T-NNN:' section whose change folder is archived. State-free.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --reconcile: report drift without writing (read-only).",
    )
    args = parser.parse_args(argv)

    if args.reconcile:
        return run_reconcile(args)

    state = read_state(args)
    if state is None:
        sys.stderr.write(f"No state file at {state_dir(args) / 'state.json'}\n")
        return EXIT_NO_STATE

    task_id = state.get("task_id", "")
    # This run sets gates.roadmap_synced (unless --no-gate), so derive against the
    # state it is about to create — otherwise the gate is still false at derive
    # time and the first run always stamps in-progress, forcing a confusing second
    # run to reach completed (T-042 G3, the "two-run dance").
    if not args.no_gate:
        state.setdefault("gates", {})["roadmap_synced"] = True
    status = derive_status(state)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    rm_path = roadmap_path(args)
    ps_path = project_status_path(args)
    if not rm_path.exists() or not ps_path.exists():
        sys.stderr.write(
            f"Missing doc: roadmap={rm_path.exists()} project-status={ps_path.exists()}\n"
        )
        return EXIT_NO_DOC

    rm_text = rm_path.read_text(encoding="utf-8")
    new_rm, title = update_roadmap(rm_text, task_id, status, today)
    if new_rm != rm_text:
        rm_path.write_text(new_rm, encoding="utf-8")

    goal = None
    if title:
        goal = f"{task_id} — {title}"

    ps_text = ps_path.read_text(encoding="utf-8")
    new_ps = update_project_status(ps_text, state, status, goal, today)
    notes_block = assemble_notes(notes_dir(args))
    if notes_block is not None:
        new_ps = update_notes_section(new_ps, notes_block)
    if new_ps != ps_text:
        ps_path.write_text(new_ps, encoding="utf-8")

    if not args.no_gate:
        set_gate_roadmap_synced(args)

    print(f"Synced roadmap + project-status for {task_id} (status={status}).")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
