#!/usr/bin/env python3
"""OpenUP input-request helper (T-033).

Maps the ``docs/input-requests/`` directory back to the delivery lanes that are
waiting on it, so the autonomous continue-loop can suspend on a question and
resume deterministically when it is answered — without the model grepping and
reasoning each cycle.

The lifecycle of an input-request (see input-request-guide.md) is::

    pending  ->  answered  ->  processed (archived)

A change folder suspends itself by setting ``awaiting-input: <path>`` in its
plan.md frontmatter and creating the request with ``status: pending`` and
``related_task: T-NNN``. While the request is ``pending`` the board reports the
lane ``suspended`` (openup-board.py). Once a human flips it to ``answered`` this
tool's ``resumable`` command surfaces the lane so /openup-next resumes it first.

Design rules (mirror scripts/openup-board.py / openup-claims.py):
  * Deterministic. Never invokes a model. Python standard library only.
  * Frontmatter parsing is *imported* from openup-claims.py, so this tool reads
    request/plan frontmatter exactly the way the board and the claim pre-flight
    do — one parser, no drift.

Subcommands:
  resumable  (default) Print ``<task>\\t<request-path>`` for every input-request
             that is ``answered`` and names a ``related_task``. Nothing if none.
  list       Print every open request (pending + answered) with its status.

Exit codes:
  0  success (always, for resumable/list — "no resumable work" is exit 0)
  2  argparse / usage error
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

# Reuse openup-claims.py (hyphenated filename → load via importlib) so request
# and plan frontmatter are parsed by the one canonical parser.
_CLAIMS_PATH = Path(__file__).resolve().parent / "openup-claims.py"
_spec = importlib.util.spec_from_file_location("openup_claims", _CLAIMS_PATH)
claims = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(claims)  # type: ignore[union-attr]

EXIT_OK = 0
EXIT_USAGE = 2

# Statuses that still live in docs/input-requests/ (processed ones are archived).
OPEN_STATUSES = {"pending", "answered"}


def requests_dir(root: Path) -> Path:
    return root / "docs" / "input-requests"


def open_requests(root: Path):
    """Yield ``(path, frontmatter)`` for each top-level input-request file.

    Only the top level of ``docs/input-requests/`` is scanned; ``archive/``
    (processed requests) is excluded. Sorted by path for deterministic output.
    """
    rdir = requests_dir(root)
    if not rdir.is_dir():
        return
    for p in sorted(rdir.glob("*.md")):
        if not p.is_file():
            continue
        fm = claims.parse_frontmatter(p)
        if fm:
            yield p, fm


def _status(fm) -> str:
    return (fm.get("status") or "").lower()


def _rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def find_resumable(root: Path):
    """Return ``[(task_id, request_rel_path)]`` for answered requests that name a
    related_task, sorted by (task_id, path). Requests without a related_task
    cannot be mapped to a lane and are skipped."""
    out = []
    for path, fm in open_requests(root):
        if _status(fm) != "answered":
            continue
        task = (fm.get("related_task") or "").strip()
        if not task:
            continue
        out.append((task, _rel(path, root)))
    out.sort()
    return out


# --------------------------------------------------------------------------
# Subcommands
# --------------------------------------------------------------------------
def resolve_root(args) -> Path:
    return Path(args.root).resolve() if args.root else claims.repo_root()


def cmd_resumable(args):
    root = resolve_root(args)
    rows = find_resumable(root)
    if args.json:
        print(json.dumps(
            [{"task": t, "request": r} for t, r in rows],
            indent=2, ensure_ascii=False))
    else:
        for task, req in rows:
            print(f"{task}\t{req}")
    return EXIT_OK


def cmd_list(args):
    root = resolve_root(args)
    rows = []
    for path, fm in open_requests(root):
        status = _status(fm)
        if status not in OPEN_STATUSES:
            continue
        rows.append({
            "status": status,
            "task": (fm.get("related_task") or "").strip() or None,
            "request": _rel(path, root),
            "title": fm.get("title"),
        })
    rows.sort(key=lambda r: (r["status"], r["request"]))
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        for r in rows:
            print(f"{r['status']}\t{r['task'] or '-'}\t{r['request']}")
    return EXIT_OK


def _slugify(title: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in title.strip()]
    slug = "".join(keep)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:48] or "input-request"


def _today() -> str:
    from datetime import date
    return date.today().isoformat()


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def insert_awaiting_input(plan_path: Path, request_rel: str) -> bool:
    """Add (or replace) an ``awaiting-input: <request_rel>`` line inside a plan's
    frontmatter block. Returns True if the file was modified.

    Coordination-frontmatter edit (like the lease) — NOT a spec behavior change,
    so it does not require a create-task-spec re-run. Same contract the
    /openup-request-input skill applies by hand.
    """
    text = plan_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return False
    close = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            close = i
            break
    if close is None:
        return False
    new_line = "awaiting-input: %s\n" % request_rel
    # Replace an existing awaiting-input line if present, else insert before close.
    for i in range(1, close):
        if lines[i].lstrip().startswith("awaiting-input:"):
            lines[i] = new_line
            plan_path.write_text("".join(lines), encoding="utf-8")
            return True
    lines.insert(close, new_line)
    plan_path.write_text("".join(lines), encoding="utf-8")
    return True


def _render_request(title, created, run_id, related_task, question, options, qtype):
    fm = [
        "---",
        'title: "%s"' % title.replace('"', "'"),
        'created: "%s"' % created,
        'created_by: "openup-agent"',
        "status: pending",
        'run_id: "%s"' % (run_id or "-"),
    ]
    if related_task:
        fm.append('related_task: "%s"' % related_task)
    fm.append("---")
    body = ["", "# Input Request — %s" % title, "", "## Question", "",
            "### Q1: %s" % title, "", "**Type**: %s" % qtype, ""]
    if qtype == "multiple-choice" and options:
        for opt in options:
            body.append("- [ ] `%s`" % opt)
        body.append("")
    body += ["**Question**: %s" % question, "", "**Answer**: _(fill in, then set "
             "`status: answered` and tell the agent to continue)_", ""]
    return "\n".join(fm + body)


def cmd_request(args):
    """Create a well-formed input-request; optionally suspend a lane (T-074).

    Deterministic creator so ANY harness (or the reference driver) can raise a
    blocking question without the Claude /openup-request-input skill. The resume
    side (``resumable``) is unchanged and treats these identically.
    """
    root = resolve_root(args)
    rdir = requests_dir(root)
    rdir.mkdir(parents=True, exist_ok=True)
    date = args.date or _today()
    qtype = "multiple-choice" if args.option else "text"
    path = rdir / ("%s-%s.md" % (date, _slugify(args.title)))
    path.write_text(_render_request(
        args.title, args.created or _now_iso(), args.run_id, args.task_id,
        args.question, args.option, qtype) + "\n", encoding="utf-8")

    suspended = False
    if args.task_id:
        plan = root / "docs" / "changes" / args.task_id / "plan.md"
        if plan.exists():
            suspended = insert_awaiting_input(plan, _rel(path, root))
    result = {"request": _rel(path, root), "task": args.task_id or None,
              "suspended": suspended}
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["request"])
    return EXIT_OK


# --------------------------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        prog="openup-input.py",
        description="Map answered input-requests back to resumable lanes.",
    )
    sub = parser.add_subparsers(dest="cmd")

    def add_common(sp):
        sp.add_argument("--root", help="Repo root override (default: git toplevel).")
        sp.add_argument("--json", action="store_true", help="Emit JSON instead of TSV.")

    p_res = sub.add_parser(
        "resumable",
        help="Print <task>\\t<request> for each answered request (nothing if none).")
    add_common(p_res)
    p_res.set_defaults(func=cmd_resumable)

    p_list = sub.add_parser("list", help="Print every open (pending/answered) request.")
    add_common(p_list)
    p_list.set_defaults(func=cmd_list)

    p_req = sub.add_parser(
        "request",
        help="Create an input-request (+ suspend a lane via --task-id).")
    add_common(p_req)
    p_req.add_argument("--title", required=True, help="Short question title.")
    p_req.add_argument("--question", required=True, help="The question text.")
    p_req.add_argument("--option", action="append", default=[],
                       help="A multiple-choice option (repeatable). Omit for a free-text question.")
    p_req.add_argument("--task-id", help="Lane to suspend (adds awaiting-input to its plan.md).")
    p_req.add_argument("--run-id", help="Originating run id (recorded in frontmatter).")
    p_req.add_argument("--date", help="Override the YYYY-MM-DD filename date (tests).")
    p_req.add_argument("--created", help="Override the created timestamp (tests).")
    p_req.set_defaults(func=cmd_request)

    return parser


def main(argv=None):
    raw = list(sys.argv[1:] if argv is None else argv)
    # Default subcommand is `resumable` when the first token isn't a known command.
    if not raw or raw[0] not in {"resumable", "list", "request"}:
        raw = ["resumable"] + raw
    args = build_parser().parse_args(raw)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
