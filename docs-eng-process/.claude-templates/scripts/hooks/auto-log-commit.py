#!/usr/bin/env python3
"""
auto-log-commit.py — OpenUP hook: fires after every Bash tool call.

On a SUCCESSFUL `git commit`, appends one schema-stable JSONL record to
docs/agent-logs/agent-runs.jsonl and sets gates.log_written true. The model
never writes the JSONL record again — this erases Kaze's 39% unlogged-run gap.

Record shape (one line):
  {"run_id", "event":"commit", "task_id", "branch", "sha",
   "model", "session_id", "ts"}

Success signal: the Bash command is a `git commit`, and the current HEAD
resolves to a SHA. Idempotency guards against double-appends: if the last
line of agent-runs.jsonl already records this SHA with event "commit", we
do nothing. This makes the hook safe even when the same commit fires the
hook more than once.

Self-reference guard: a commit that touched ONLY the run log itself is pure
bookkeeping (it persists a previously auto-logged line). Logging it again
would re-dirty the log and tail-chase forever, so such commits are skipped.
This lets a final "commit the log" reach a genuinely clean tree.

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

LOG_REL = "docs/agent-logs/agent-runs.jsonl"


def run(cmd: str, cwd: str) -> tuple[int, str]:
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True
    )
    return result.returncode, result.stdout.strip()


def state_get(cwd: str, key: str) -> tuple[int, str]:
    script = Path(cwd) / "scripts" / "openup-state.py"
    return run(f'python3 "{script}" get {key}', cwd)


def set_gate(cwd: str, name: str, value: str) -> None:
    script = Path(cwd) / "scripts" / "openup-state.py"
    run(f'python3 "{script}" set-gate {name} {value}', cwd)


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


def commit_only_touches_log(cwd: str, sha: str) -> bool:
    """True if the commit at <sha> changed ONLY the run log itself.

    Such a commit is pure bookkeeping (persisting a prior auto-logged line);
    logging it again would re-dirty the log and tail-chase forever. Uses
    diff-tree against the first parent; the root commit (no parent) lists its
    whole tree, which will not be log-only, so it is logged normally.
    """
    rc, out = run(f"git diff-tree --no-commit-id --name-only -r {sha}", cwd)
    if rc != 0:
        return False
    files = [ln.strip() for ln in out.splitlines() if ln.strip()]
    return files == [LOG_REL]


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

        # Resolve HEAD SHA. If this fails, there is nothing to log.
        rc, sha = run("git rev-parse HEAD", cwd)
        sha = sha.strip()
        if rc != 0 or not sha:
            sys.exit(0)

        # Self-reference guard: skip commits that only touched the run log —
        # logging them would re-dirty it and tail-chase forever.
        if commit_only_touches_log(cwd, sha):
            sys.exit(0)

        log_path = Path(cwd) / LOG_REL

        # Idempotency: skip if this SHA is already the last commit record.
        if last_logged_sha(log_path) == sha:
            sys.exit(0)

        # Gather fields.
        _, branch = run("git rev-parse --abbrev-ref HEAD", cwd)
        branch = branch.strip()

        scode, task_id = state_get(cwd, "task_id")
        task_id = task_id.strip() if scode == 0 else None

        sidcode, session_id = state_get(cwd, "session_id")
        session_id = session_id.strip() if sidcode == 0 else None
        if session_id in ("null", ""):
            session_id = None

        model = payload.get("model") or payload.get("permission_mode_model")
        if not model:
            model = None

        ts = (
            payload.get("ts")
            or payload.get("timestamp")
            or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        )

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

        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

        # Flip the log_written gate (best-effort; only if state exists).
        if scode == 0:
            set_gate(cwd, "log_written", "true")

        sys.exit(0)

    except SystemExit:
        raise
    except Exception:
        sys.exit(0)  # fail open


if __name__ == "__main__":
    main()
