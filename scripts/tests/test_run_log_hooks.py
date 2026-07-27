"""End-to-end tests for the run-log hook pair (T-140).

Drives the REAL hook scripts — `auto-log-commit.py` (PostToolUse) and
`stage-run-log.py` (PreToolUse) — with realistic payloads against a throwaway
git repo, asserting the property the task exists for: a successful commit never
leaves `docs/agent-logs/` dirty, and the record lands inside a later commit.

These complement `test_openup_runlog.py`, which unit-tests the drain logic.

NB: the hooks are read from the repo's gitignored `.claude/scripts/hooks/`, which
`sync-templates-to-claude.sh` renders from the pack. If that sync has not been
run the tests skip rather than fail — the pack copy is the source of truth.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
POST_HOOK = REPO / ".claude/scripts/hooks/auto-log-commit.py"
PRE_HOOK = REPO / ".claude/scripts/hooks/stage-run-log.py"
RUNLOG = REPO / "scripts/openup-runlog.py"

pytestmark = pytest.mark.skipif(
    not (POST_HOOK.exists() and PRE_HOOK.exists()),
    reason="hooks not synced into .claude/ — run scripts/sync-templates-to-claude.sh",
)

# Split so this file's own source can't trip a `git commit` matcher in tooling
# that scans command text.
COMMIT = "git " + "commit"


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def fire(hook, repo, command, response=None):
    payload = {"tool_name": "Bash", "cwd": str(repo),
               "tool_input": {"command": command}}
    if response is not None:
        payload["tool_response"] = response
    return subprocess.run([sys.executable, str(hook)], input=json.dumps(payload),
                          capture_output=True, text=True, cwd=repo)


def queue_shas(repo):
    q = repo / ".openup" / "run-log-pending.jsonl"
    if not q.exists():
        return []
    return [json.loads(l)["sha"] for l in q.read_text().splitlines() if l.strip()]


def shard_records(repo):
    d = repo / "docs" / "agent-logs" / "runs"
    if not d.exists():
        return []
    return [json.loads(ln)
            for f in sorted(d.iterdir())
            for ln in f.read_text().splitlines() if ln.strip()]


def dirty_logs(repo):
    return git(repo, "status", "--porcelain", "--", "docs/agent-logs/").stdout.strip()


@pytest.fixture
def fixture_repo(tmp_path):
    repo = tmp_path / "proj"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy(RUNLOG, repo / "scripts" / "openup-runlog.py")
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "T")
    (repo / ".gitignore").write_text(".openup/\n")
    (repo / "README.md").write_text("hello\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    return repo


def test_post_commit_hook_queues_without_dirtying_the_tree(fixture_repo):
    """R1 + R2 — the defect itself: logging must not dirty docs/agent-logs/."""
    fire(POST_HOOK, fixture_repo, f'{COMMIT} -m "work"',
         {"returncode": 0, "stdout": "1 file changed"})

    head = git(fixture_repo, "rev-parse", "HEAD").stdout.strip()
    assert queue_shas(fixture_repo) == [head]
    assert shard_records(fixture_repo) == []
    assert dirty_logs(fixture_repo) == ""


def test_pre_commit_hook_drains_stages_and_lands_inside_the_commit(fixture_repo):
    """R3 — the record reaches the shard *inside* the next commit."""
    fire(POST_HOOK, fixture_repo, f'{COMMIT} -m "work"', {"returncode": 0})
    head = git(fixture_repo, "rev-parse", "HEAD").stdout.strip()

    fire(PRE_HOOK, fixture_repo, f'{COMMIT} -m "next"')

    records = shard_records(fixture_repo)
    assert [r["sha"] for r in records] == [head]
    assert queue_shas(fixture_repo) == []
    staged = git(fixture_repo, "diff", "--cached", "--name-only").stdout
    assert "docs/agent-logs/runs/" in staged

    git(fixture_repo, "commit", "-q", "-m", "second")
    in_commit = git(fixture_repo, "show", "--name-only", "--format=", "HEAD").stdout
    assert "docs/agent-logs/runs/" in in_commit
    assert dirty_logs(fixture_repo) == ""


def test_pathspec_limited_commit_does_not_drain(fixture_repo):
    """R7 — staging a shard a pathspec commit would ignore recreates the defect."""
    fire(POST_HOOK, fixture_repo, f'{COMMIT} -m "work"', {"returncode": 0})
    head = git(fixture_repo, "rev-parse", "HEAD").stdout.strip()

    fire(PRE_HOOK, fixture_repo, f'{COMMIT} -m "x" -- scripts/foo.py')

    assert queue_shas(fixture_repo) == [head]      # queue untouched
    assert shard_records(fixture_repo) == []       # nothing written or staged


def test_sha_already_in_a_shard_is_not_requeued(fixture_repo):
    """R4 — double-firing the hook must not duplicate a record."""
    fire(POST_HOOK, fixture_repo, f'{COMMIT} -m "work"', {"returncode": 0})
    fire(PRE_HOOK, fixture_repo, f'{COMMIT} -m "next"')
    git(fixture_repo, "commit", "-q", "-m", "second")

    fire(POST_HOOK, fixture_repo, f'{COMMIT} -m "again"', {"returncode": 0})

    # HEAD moved to the 'second' commit, which is logs-only → skipped outright.
    assert queue_shas(fixture_repo) == []
    assert len(shard_records(fixture_repo)) == 1


def test_logs_only_commit_is_not_logged(fixture_repo):
    """The self-reference guard still holds: bookkeeping commits get no record."""
    runs = fixture_repo / "docs" / "agent-logs" / "runs"
    runs.mkdir(parents=True)
    (runs / "2026-07-27-x.jsonl").write_text("")
    git(fixture_repo, "add", "-A")
    git(fixture_repo, "commit", "-q", "-m", "logs only")

    fire(POST_HOOK, fixture_repo, f'{COMMIT} -m "logs only"', {"returncode": 0})

    assert queue_shas(fixture_repo) == []


def test_a_failed_commit_is_not_logged(fixture_repo):
    """R6-adjacent — 'nothing to commit' must not produce a record."""
    fire(POST_HOOK, fixture_repo, f'{COMMIT} -m "x"',
         {"returncode": 1, "stdout": "nothing to commit, working tree clean"})
    assert queue_shas(fixture_repo) == []


@pytest.mark.parametrize("hook", [POST_HOOK, PRE_HOOK])
def test_hooks_fail_open_on_a_corrupt_queue(fixture_repo, hook):
    """R6 — a logging bug must never block a commit."""
    (fixture_repo / ".openup").mkdir(exist_ok=True)
    (fixture_repo / ".openup" / "run-log-pending.jsonl").write_text("{not json\n")

    res = fire(hook, fixture_repo, f'{COMMIT} -m "x"', {"returncode": 0})

    assert res.returncode == 0, res.stderr


@pytest.mark.parametrize("hook", [POST_HOOK, PRE_HOOK])
def test_hooks_ignore_non_commit_commands(fixture_repo, hook):
    res = fire(hook, fixture_repo, "ls -la", {"returncode": 0})
    assert res.returncode == 0
    assert queue_shas(fixture_repo) == []
    assert shard_records(fixture_repo) == []
