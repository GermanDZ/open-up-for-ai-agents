#!/usr/bin/env python3
"""Deterministic scribe writes for OpenUP completion steps.

Two mechanical writes in ``/openup-complete-task`` used to be delegated to the
``openup-scribe`` *agent* (a haiku model round-trip) even though the path, the
collision rule, and the exact block format are fully specified — the model only
ever supplied the content. Doing them in a script removes the round-trip and,
more importantly, removes format/path drift: the layout can no longer vary run
to run.

The caller still decides the *content* (the iteration summary, the learnings);
this tool owns the *mechanics* (where it goes, the dated filename, the
collision suffix, the block structure).

Design rules (matching the other ``scripts/openup-*.py`` tools):
  * Deterministic. Never invokes a model.
  * Python standard library only.

Subcommands:
  status-note  Write a lane-owned, conflict-free iteration note shard under
               docs/status-notes/ (sync-status.py assembles the shared view).
  learnings    Append a dated entry to .claude/memory/iteration-learnings.md.

Usage:
  python3 scripts/openup-scribe.py status-note --task-id T-001 --body "- ..."
  python3 scripts/openup-scribe.py learnings --task-id T-001 --title "..." \\
      --what-worked "..." --decisions "..." --gotchas "..." --conventions "..."

Exit codes:
  0  written
  2  usage error
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent


def _today(args):
    return args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _read_body(value):
    """Body from --body, or stdin when --body is '-' or omitted."""
    if value and value != "-":
        return value.rstrip("\n") + "\n"
    return sys.stdin.read().rstrip("\n") + "\n"


def cmd_status_note(args):
    out_dir = Path(args.dir) if args.dir else REPO_ROOT / "docs" / "status-notes"
    out_dir.mkdir(parents=True, exist_ok=True)
    date = _today(args)
    body = _read_body(args.body)

    base = out_dir / ("%s-%s.md" % (date, args.task_id))
    target = base
    if target.exists():
        # Collision rule from /openup-complete-task: add -HHMM, then -HHMMSS.
        now = datetime.now(timezone.utc)
        for stamp in (now.strftime("%H%M"), now.strftime("%H%M%S")):
            cand = out_dir / ("%s-%s-%s.md" % (date, args.task_id, stamp))
            if not cand.exists():
                target = cand
                break
        else:
            # Extremely unlikely; fall back to a numeric suffix.
            n = 2
            while (out_dir / ("%s-%s-%d.md" % (date, args.task_id, n))).exists():
                n += 1
            target = out_dir / ("%s-%s-%d.md" % (date, args.task_id, n))

    target.write_text(body, encoding="utf-8")
    print(str(target.relative_to(REPO_ROOT)) if target.is_relative_to(REPO_ROOT) else target)
    return 0


def cmd_learnings(args):
    path = Path(args.file) if args.file else REPO_ROOT / ".claude" / "memory" / "iteration-learnings.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    date = _today(args)

    entry = (
        "\n## [%s] %s: %s\n"
        "- **What worked**: %s\n"
        "- **Decisions made**: %s\n"
        "- **Gotchas**: %s\n"
        "- **Conventions established**: %s\n"
        % (
            date, args.task_id, args.title,
            args.what_worked, args.decisions, args.gotchas, args.conventions,
        )
    )

    header = "# Iteration Learnings\n"
    if not path.exists():
        path.write_text(header + entry, encoding="utf-8")
    else:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(entry)
    print("appended learnings for %s to %s" % (args.task_id, path))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description="Deterministic OpenUP scribe writes.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sn = sub.add_parser("status-note", help="write a dated status-note shard")
    sn.add_argument("--task-id", required=True)
    sn.add_argument("--body", help="note content (default: read from stdin)")
    sn.add_argument("--date", help="YYYY-MM-DD (default: today UTC)")
    sn.add_argument("--dir", help="override output dir (default: docs/status-notes)")
    sn.set_defaults(func=cmd_status_note)

    ln = sub.add_parser("learnings", help="append a dated iteration-learnings entry")
    ln.add_argument("--task-id", required=True)
    ln.add_argument("--title", required=True)
    ln.add_argument("--what-worked", default="")
    ln.add_argument("--decisions", default="")
    ln.add_argument("--gotchas", default="")
    ln.add_argument("--conventions", default="")
    ln.add_argument("--date", help="YYYY-MM-DD (default: today UTC)")
    ln.add_argument("--file", help="override target file")
    ln.set_defaults(func=cmd_learnings)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
