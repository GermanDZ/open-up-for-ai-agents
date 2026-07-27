#!/usr/bin/env python3
"""
auto-log-commit.py — OpenUP hook: fires after every Bash tool call.

On a SUCCESSFUL `git commit`, QUEUES one schema-stable JSONL record and sets
gates.log_written true. The model never writes the JSONL record again — this
erases Kaze's 39% unlogged-run gap.

T-140 — the record is queued, never written to the tracked shard from here. A
commit can never contain its own log record (the record carries the commit's
SHA, and the SHA hashes the tree that would hold it), so a PostToolUse write
into docs/agent-logs/ left the tree dirty and forced a follow-up "sweep" commit
on every lane. The record now goes to the UNTRACKED queue
`<main-repo-root>/.openup/run-log-pending.jsonl` (via `scripts/openup-runlog.py
append`); the PreToolUse hook `stage-run-log.py` drains it into the lane shard
and stages it just before the NEXT commit. Records therefore land inside a
commit, and a successful commit never dirties a tracked file.

Record shape (one line):
  {"run_id", "event":"commit", "task_id", "branch", "sha",
   "model", "session_id", "ts"}

Success signal: the Bash command is a `git commit`, and the current HEAD
resolves to a SHA. Idempotency guards against double-appends: if this SHA is
already recorded — in the lane shard, or still sitting in the queue — we do
nothing. This makes the hook safe even when the same commit fires the hook
more than once.

Self-reference guard: a commit that touched ONLY audit-trail files (anything
under docs/agent-logs/) is pure bookkeeping and is not logged. With the queue
this is no longer load-bearing (nothing here dirties the shard), but it is kept
so a logs-only commit does not generate a record about itself.

Exit codes:
  0 — always (PostToolUse cannot block; this hook only appends)

Fail-open: any internal error is swallowed; a buggy logger must never break
the user's session.

Hook event: PostToolUse / Bash
"""

import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

COMMIT_RE = re.compile(r"\bgit\b.*\bcommit\b", re.DOTALL)

LOG_DIR = "docs/agent-logs/"
RUNS_REL = "docs/agent-logs/runs"  # T-046: lane-owned run shards live here


def shard_key(task_id, branch):
    """Lane key for the run shard filename (T-046) — must match
    openup-state.py `_shard_key` so both writers target the same lane file."""
    raw = (task_id or "").strip() or (branch or "").strip() or "no-task"
    if raw in ("null",):
        raw = (branch or "no-task").strip() or "no-task"
    slug = re.sub(r"[^0-9A-Za-z._-]+", "-", raw).strip("-")
    return slug or "no-task"


def shard_path(cwd: str, task_id, branch, ts: str) -> Path:
    """`docs/agent-logs/runs/<UTC-date>-<key>.jsonl` for this lane (T-046)."""
    return Path(cwd) / RUNS_REL / f"{ts[:10]}-{shard_key(task_id, branch)}.jsonl"


def run(cmd: str, cwd: str) -> tuple[int, str]:
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True
    )
    return result.returncode, result.stdout.strip()


def state_get(cwd: str, key: str) -> tuple[int, str]:
    script = Path(cwd) / "scripts" / "openup-state.py"
    return run(f'python3 "{script}" get {key}', cwd)


def resolve_state_root(cwd: str) -> str:
    """Repo/worktree root that holds the active iteration state.

    With worktree-per-task, .openup/state.json lives in the task worktree while
    the harness cwd may stay pinned to the main repo — leaving the commit record
    with task_id null. Prefer cwd if it has state; else scan linked worktrees
    (`git worktree list`) for one that does, preferring the worktree whose branch
    matches HEAD. Fail-safe: cwd when nothing resolves (T-042 Fix-7b).
    """
    if (Path(cwd) / ".openup" / "state.json").exists():
        return cwd
    rc, out = run("git worktree list --porcelain", cwd)
    if rc != 0 or not out:
        return cwd
    candidates, path = [], None
    for line in out.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):].strip()
        elif line.startswith("branch ") and path:
            candidates.append((path, line[len("branch "):].strip()))
            path = None
        elif not line.strip():
            path = None
    with_state = [(p, b) for (p, b) in candidates
                  if (Path(p) / ".openup" / "state.json").exists()]
    if not with_state:
        return cwd
    _, cur = run("git rev-parse --abbrev-ref HEAD", cwd)
    cur = cur.strip()
    for p, b in with_state:
        if b == cur or b.endswith("/" + cur):
            return p
    return with_state[0][0]


def set_gate(cwd: str, name: str, value: str) -> None:
    script = Path(cwd) / "scripts" / "openup-state.py"
    run(f'python3 "{script}" set-gate {name} {value}', cwd)


def _worktree_heads(cwd: str) -> list[tuple[str, str]]:
    """[(path, head_sha)] for every linked worktree. Parses
    `git worktree list --porcelain`; a detached/bare entry with no HEAD is
    skipped. Empty on any failure."""
    rc, out = run("git worktree list --porcelain", cwd)
    if rc != 0 or not out:
        return []
    res, path = [], None
    for line in out.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):].strip()
        elif line.startswith("HEAD ") and path:
            res.append((path, line[len("HEAD "):].strip()))
            path = None
        elif not line.strip():
            path = None
    return res


def _committer_ts(cwd: str, sha: str) -> int:
    """Committer timestamp (epoch secs) of <sha>, or -1 if unresolvable."""
    rc, out = run(f"git show -s --format=%ct {sha}", cwd)
    try:
        return int(out.strip()) if rc == 0 and out.strip() else -1
    except ValueError:
        return -1


def resolve_commit_root(cwd: str) -> tuple[str, str]:
    """Return (root, sha) for the worktree that just received the commit.

    The harness cwd stays pinned to the main checkout while OpenUP skills run
    `cd <worktree> && git commit`, so trusting `payload.cwd` logs the commit into
    the WRONG tree (main's HEAD, main's shard) — which dirties main and blocks
    the next pull (T-068). A freshly-made commit is always the newest across
    worktrees, so we pick the worktree whose HEAD has the max committer
    timestamp — no command parsing, no cross-invocation state.

    Fallback: ≤1 worktree (the plain no-worktree repo) or any enumeration
    failure → (cwd, HEAD-of-cwd), i.e. exactly today's behavior — this change is
    a strict superset.
    """
    heads = _worktree_heads(cwd)
    if len(heads) <= 1:
        rc, sha = run("git rev-parse HEAD", cwd)
        return cwd, (sha.strip() if rc == 0 else "")
    best_path, best_sha, best_ts = cwd, "", -2
    for path, sha in heads:
        ts = _committer_ts(path, sha)
        if ts > best_ts:
            best_path, best_sha, best_ts = path, sha, ts
    return best_path, best_sha


def commit_succeeded(payload: dict, command: str) -> bool:
    """Heuristic: a commit command whose tool_response shows no failure.

    PostToolUse only fires after the tool ran. We treat the commit as
    successful unless the response clearly signals failure (non-zero / error).
    The HEAD-SHA idempotency guard downstream prevents stale/no-op appends.
    """
    resp = payload.get("tool_response", payload.get("tool_output", {}))
    text = ""
    if isinstance(resp, dict):
        # Common shapes: {"stdout","stderr"}, {"output"}, {"success":bool}
        if resp.get("success") is False:
            return False
        if resp.get("interrupted") is True:
            return False
        text = " ".join(
            str(resp.get(k, "")) for k in ("stdout", "stderr", "output", "error")
        )
        rc = resp.get("returncode", resp.get("exit_code"))
        if isinstance(rc, int) and rc != 0:
            return False
    elif isinstance(resp, str):
        text = resp

    low = text.lower()
    # Obvious failure markers from git.
    if "nothing to commit" in low or "no changes added to commit" in low:
        return False
    return True


def commit_only_touches_logs(cwd: str, sha: str) -> bool:
    """True if the commit at <sha> changed ONLY audit-trail files.

    A commit touching nothing but files under docs/agent-logs/ — the JSONL run
    log AND the markdown narrative logs that complete-task writes — is pure
    bookkeeping: it persists previously auto-logged lines. Logging it again
    would append a fresh record and re-dirty agent-runs.jsonl, tail-chasing
    forever. Skipping such commits lets a closing "commit the logs" reach a
    genuinely clean tree even when the markdown log is bundled with the JSONL
    (the complete-task pattern), not just when the JSONL is committed alone.

    Uses diff-tree against the first parent; the root commit (no parent) lists
    its whole tree, which will not be logs-only, so it is logged normally.
    """
    rc, out = run(f"git diff-tree --no-commit-id --name-only -r {sha}", cwd)
    if rc != 0:
        return False
    files = [ln.strip() for ln in out.splitlines() if ln.strip()]
    return bool(files) and all(f.startswith(LOG_DIR) for f in files)


def queue_record(root: str, record: dict) -> bool:
    """Queue the record via scripts/openup-runlog.py (T-140).

    Writes to the UNTRACKED `<main-root>/.openup/run-log-pending.jsonl`, so a
    successful commit never dirties a tracked file. Returns False if the queue
    script is missing or errored — the caller then simply does not flip the gate.
    """
    script = Path(root) / "scripts" / "openup-runlog.py"
    if not script.exists():
        return False
    try:
        res = subprocess.run(
            ["python3", str(script), "--cwd", root, "append", "--record",
             json.dumps(record)],
            cwd=root, capture_output=True, text=True,
        )
        return res.returncode == 0
    except Exception:
        return False


def pending_has_sha(root: str, sha: str) -> bool:
    """True if this SHA is already sitting in the queue (double-fire guard)."""
    try:
        script = Path(root) / "scripts" / "openup-runlog.py"
        res = subprocess.run(["python3", str(script), "--cwd", root, "path"],
                             cwd=root, capture_output=True, text=True)
        if res.returncode != 0 or not res.stdout.strip():
            return False
        queue = Path(res.stdout.strip())
        if not queue.exists():
            return False
        return any(
            json.loads(ln).get("sha") == sha
            for ln in queue.read_text(encoding="utf-8").splitlines()
            if ln.strip().startswith("{")
        )
    except Exception:
        return False


def last_logged_sha(log_path: Path) -> str | None:
    """Return the sha recorded on the last commit-event line, or None."""
    try:
        if not log_path.exists():
            return None
        with log_path.open("r", encoding="utf-8") as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.strip()]
        if not lines:
            return None
        try:
            rec = json.loads(lines[-1])
        except json.JSONDecodeError:
            return None
        if rec.get("event") == "commit":
            return rec.get("sha")
    except OSError:
        return None
    return None


def main() -> None:
    try:
        raw = sys.stdin.read().strip()
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {}

        if payload.get("tool_name", "") != "Bash":
            sys.exit(0)

        command = payload.get("tool_input", {}).get("command", "")
        if not COMMIT_RE.search(command):
            sys.exit(0)

        cwd = payload.get("cwd", os.getcwd())

        if not commit_succeeded(payload, command):
            sys.exit(0)

        # Resolve the worktree the commit actually landed in (T-068). The harness
        # cwd stays pinned to the main checkout during `cd <worktree> && git
        # commit`, so using it here would read main's HEAD and append the record
        # into main's shard — dirtying main and blocking the next pull. `root` is
        # the worktree whose HEAD is the just-made commit; `sha` is that commit.
        root, sha = resolve_commit_root(cwd)
        if not sha:
            sys.exit(0)

        # Self-reference guard: skip commits that only touched audit-trail
        # files (anything under docs/agent-logs/, which includes the run shards)
        # — logging them would re-dirty the shard and tail-chase forever.
        if commit_only_touches_logs(root, sha):
            sys.exit(0)

        # Gather fields — from the commit's worktree, not the pinned cwd.
        _, branch = run("git rev-parse --abbrev-ref HEAD", root)
        branch = branch.strip()

        # Read iteration state from the worktree that owns it, not a cwd pinned
        # to the main repo (T-042 Fix-7b) — otherwise commits log task_id null.
        sroot = resolve_state_root(root)
        scode, task_id = state_get(sroot, "task_id")
        task_id = task_id.strip() if scode == 0 else None
        if task_id in ("null", ""):
            task_id = None

        ts = (
            payload.get("ts")
            or payload.get("timestamp")
            or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        # T-046: the record belongs to the LANE-OWNED shard, never the shared
        # agent-runs.jsonl (a gitignored derived view). T-140: we do not write
        # that shard here — a PostToolUse write would dirty the tree the commit
        # just cleaned. Idempotency therefore checks BOTH the shard (already
        # flushed) and the queue (flushed pending).
        log_path = shard_path(root, task_id, branch, ts)
        if last_logged_sha(log_path) == sha or pending_has_sha(root, sha):
            sys.exit(0)

        sidcode, session_id = state_get(sroot, "session_id")
        session_id = session_id.strip() if sidcode == 0 else None
        if session_id in ("null", ""):
            session_id = None

        model = payload.get("model") or payload.get("permission_mode_model")
        if not model:
            model = None

        record = {
            "run_id": uuid.uuid4().hex,
            "event": "commit",
            "task_id": task_id,
            "branch": branch,
            "sha": sha,
            "model": model,
            "session_id": session_id,
            "ts": ts,
        }

        # T-140: queue it (untracked); stage-run-log.py drains it into the shard
        # immediately before the next commit, so it lands INSIDE that commit.
        if not queue_record(root, record):
            sys.exit(0)

        # Flip the log_written gate (best-effort; only if state exists).
        if scode == 0:
            set_gate(sroot, "log_written", "true")

        sys.exit(0)

    except SystemExit:
        raise
    except Exception:
        sys.exit(0)  # fail open


if __name__ == "__main__":
    main()
