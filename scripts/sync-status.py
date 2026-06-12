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
TRACK_REQUIRED = {
    "quick": ["log_written", "roadmap_synced"],
    "standard": ["team_deployed", "log_written", "roadmap_synced"],
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
            break
    return "".join(lines), title


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
    args = parser.parse_args(argv)

    state = read_state(args)
    if state is None:
        sys.stderr.write(f"No state file at {state_dir(args) / 'state.json'}\n")
        return EXIT_NO_STATE

    task_id = state.get("task_id", "")
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
