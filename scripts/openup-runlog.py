#!/usr/bin/env python3
"""
openup-runlog.py — the run-log pending queue (T-140).

A commit can never contain its own log record: the record carries the commit's
SHA, and the SHA hashes the tree that would hold the record. So `auto-log-commit.py`
(a PostToolUse hook) could only ever append AFTER the commit landed, leaving
`docs/agent-logs/` dirty and forcing a follow-up "sweep" commit on every lane.

This module splits the write in two:

  append  — the post-commit hook queues the record into an UNTRACKED file,
            `<main-repo-root>/.openup/run-log-pending.jsonl` (`/.openup/` is
            gitignored), so a successful commit never dirties a tracked file.
  flush   — the pre-commit hook drains the queue into each record's OWN lane
            shard (`docs/agent-logs/runs/<UTC-date>-<lane-key>.jsonl`, routed by
            the record's task_id/branch), `git add`s the touched shards, and
            empties the queue — so the records land INSIDE the commit that is
            about to be created.

Steady state: every commit carries the records of all prior commits, the tree is
never dirty, and the queue holds at most the trailing record (drained by the next
commit anywhere in the repo).

Exit code: always 0. A logging bug must never break a session or block a commit.
"""

import argparse
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

PENDING_REL = ".openup/run-log-pending.jsonl"
RUNS_REL = "docs/agent-logs/runs"

COMMIT_RE = re.compile(r"\bgit\b.*\bcommit\b", re.DOTALL)

# `git commit` options that consume the FOLLOWING token as their value. Anything
# left over that is not a flag is a pathspec.
LONG_VALUE_OPTS = {
    "--message", "--file", "--author", "--date", "--reuse-message",
    "--reedit-message", "--template", "--cleanup", "--fixup", "--squash",
    "--trailer", "--pathspec-from-file", "--gpg-sign", "--untracked-files",
}
SHORT_VALUE_OPTS = set("mFCct")


def run(argv, cwd):
    """Run a command as an argv list — never through a shell, so a record-derived
    shard path can't become a shell metacharacter."""
    try:
        r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
        return r.returncode, r.stdout.strip()
    except Exception:
        return 1, ""


def main_repo_root(cwd):
    """Root of the MAIN checkout, even when called from a linked worktree.

    `--git-common-dir` points at the shared `.git` (the main repo's), so its
    parent is the main root. The queue lives there so records survive the
    worktree teardown `/openup-complete-task` performs.
    """
    rc, out = run(["git", "rev-parse", "--path-format=absolute",
                   "--git-common-dir"], cwd)
    if rc != 0 or not out:
        return Path(cwd)
    p = Path(out)
    return p.parent if p.name == ".git" else p


def pending_path(cwd):
    return main_repo_root(cwd) / PENDING_REL


def shard_key(task_id, branch):
    """Lane key for the shard filename — must match `_shard_key` in
    openup-state.py and `shard_key` in auto-log-commit.py."""
    raw = (task_id or "").strip() or (branch or "").strip() or "no-task"
    if raw == "null":
        raw = (branch or "no-task").strip() or "no-task"
    slug = re.sub(r"[^0-9A-Za-z._-]+", "-", raw).strip("-")
    return slug or "no-task"


def shard_for(record):
    ts = str(record.get("ts") or "")
    key = shard_key(record.get("task_id"), record.get("branch"))
    return f"{RUNS_REL}/{ts[:10]}-{key}.jsonl"


def commit_segment(command):
    """The `git commit …` sub-command of a possibly-compound shell command."""
    for seg in re.split(r"&&|\|\||;|\|", command):
        if COMMIT_RE.search(seg):
            return seg
    return None


def commit_has_pathspec(command):
    """True if this `git commit` limits itself to explicit paths.

    Staging a shard for a pathspec-limited commit would leave it staged but
    uncommitted — exactly the dirty tree this feature removes — so such a commit
    must not drain. Unparseable input returns True (skip the drain; the records
    simply wait for the next commit).
    """
    seg = commit_segment(command)
    if seg is None:
        return True
    try:
        tokens = shlex.split(seg)
    except ValueError:
        return True
    try:
        idx = next(i for i, t in enumerate(tokens) if t == "commit")
    except StopIteration:
        return True
    rest = tokens[idx + 1:]
    i = 0
    while i < len(rest):
        tok = rest[i]
        if tok == "--":
            return i + 1 < len(rest)          # `--` with anything after it
        if tok.startswith("--"):
            if "=" not in tok and tok in LONG_VALUE_OPTS:
                i += 1                         # consume its value
        elif tok.startswith("-") and len(tok) > 1:
            body = tok[1:]
            for pos, ch in enumerate(body):
                if ch in SHORT_VALUE_OPTS:
                    if pos == len(body) - 1:
                        i += 1                 # value is the next token
                    break                      # value is the rest of this token
        else:
            return True                        # a bare positional = pathspec
        i += 1
    return False


def read_pending(path):
    records = []
    try:
        if not path.exists():
            return records
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue                       # tolerate a torn/corrupt line
            if isinstance(rec, dict):
                records.append(rec)
    except OSError:
        return []
    return records


def shard_identities(shard_file):
    """{(event, sha)} already recorded in this shard — the dedupe key."""
    seen = set()
    try:
        if not shard_file.exists():
            return seen
        for line in shard_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict) and rec.get("sha"):
                seen.add((rec.get("event"), rec.get("sha")))
    except OSError:
        pass
    return seen


def cmd_append(args):
    raw = args.record if args.record is not None else sys.stdin.read()
    raw = (raw or "").strip()
    if not raw:
        return 0
    try:
        json.loads(raw)                        # refuse to queue non-JSON
    except json.JSONDecodeError:
        return 0
    path = pending_path(args.cwd)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(raw.replace("\n", " ") + "\n")
    except OSError:
        pass
    return 0


def cmd_flush(args):
    if args.command is not None and commit_has_pathspec(args.command):
        return 0
    worktree = Path(args.worktree or args.cwd)
    path = pending_path(args.cwd)
    records = read_pending(path)
    if not records:
        return 0

    touched, batch_seen = [], {}
    for rec in records:
        rel = shard_for(rec)
        shard_file = worktree / rel
        if rel not in batch_seen:
            batch_seen[rel] = shard_identities(shard_file)
        ident = (rec.get("event"), rec.get("sha"))
        if ident[1] and ident in batch_seen[rel]:
            continue                            # already in the shard — drop it
        try:
            shard_file.parent.mkdir(parents=True, exist_ok=True)
            with shard_file.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
        except OSError:
            continue
        if ident[1]:
            batch_seen[rel].add(ident)
        if rel not in touched:
            touched.append(rel)

    try:
        path.write_text("", encoding="utf-8")   # queue drained
    except OSError:
        pass

    if touched and not args.no_add:
        run(["git", "add", "--"] + touched, str(worktree))
    for rel in touched:
        print(rel)
    return 0


def cmd_path(args):
    print(pending_path(args.cwd))
    return 0


def build_parser():
    p = argparse.ArgumentParser(description="Run-log pending queue (T-140).")
    p.add_argument("--cwd", default=".", help="Directory to resolve git from.")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("append", help="Queue one JSONL record (untracked).")
    a.add_argument("--record", default=None, help="JSON record; default stdin.")
    a.set_defaults(func=cmd_append)

    f = sub.add_parser("flush", help="Drain the queue into lane shards and stage them.")
    f.add_argument("--worktree", default=None, help="Worktree receiving the shards.")
    f.add_argument("--command", default=None,
                   help="The git-commit command about to run; skips on a pathspec.")
    f.add_argument("--no-add", action="store_true", help="Do not `git add` the shards.")
    f.set_defaults(func=cmd_flush)

    s = sub.add_parser("path", help="Print the pending-queue path.")
    s.set_defaults(func=cmd_path)
    return p


def main():
    try:
        args = build_parser().parse_args()
        args.func(args)
    except SystemExit:
        raise
    except Exception:
        pass                                    # fail open, always
    sys.exit(0)


if __name__ == "__main__":
    main()
