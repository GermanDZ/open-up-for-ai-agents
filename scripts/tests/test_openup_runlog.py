"""Tests for scripts/openup-runlog.py — the run-log pending queue (T-140).

Covers the contract the spec's requirements state: records queue to an untracked
file, drain into their OWN lane shard, dedupe by SHA, tolerate corruption, skip a
pathspec-limited commit, and never raise.
"""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "openup-runlog.py"


def load_module():
    spec = importlib.util.spec_from_file_location("openup_runlog", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


runlog = load_module()


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True,
                   capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    """A real git repo — the queue path is derived from --git-common-dir."""
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-q")
    git(r, "config", "user.email", "t@example.com")
    git(r, "config", "user.name", "T")
    (r / "README.md").write_text("x\n")
    git(r, "add", "README.md")
    git(r, "commit", "-q", "-m", "init")
    return r


def record(sha, task_id="T-140", branch="fix/T-140", ts="2026-07-27T09:00:00Z",
           event="commit"):
    return {"run_id": sha, "event": event, "task_id": task_id, "branch": branch,
            "sha": sha, "model": None, "session_id": None, "ts": ts}


def run_cli(repo, *args):
    return subprocess.run(
        ["python3", str(SCRIPT), "--cwd", str(repo), *args],
        cwd=repo, capture_output=True, text=True,
    )


def shard(repo, name):
    return repo / "docs" / "agent-logs" / "runs" / name


# --- queue location -------------------------------------------------------


def test_pending_path_is_untracked_and_under_main_root(repo):
    p = runlog.pending_path(str(repo))
    assert p == repo / ".openup" / "run-log-pending.jsonl"


def test_pending_path_from_worktree_points_at_main_root(repo, tmp_path):
    """A linked worktree must queue into the MAIN root, so records survive the
    worktree teardown that /openup-complete-task performs."""
    wt = tmp_path / "proj-T-1"
    git(repo, "worktree", "add", "-q", str(wt), "-b", "lane")
    assert runlog.pending_path(str(wt)) == repo / ".openup" / "run-log-pending.jsonl"


# --- append ---------------------------------------------------------------


def test_append_queues_one_line_and_touches_no_shard(repo):
    run_cli(repo, "append", "--record", json.dumps(record("aaa")))
    pending = repo / ".openup" / "run-log-pending.jsonl"
    assert len(pending.read_text().strip().splitlines()) == 1
    assert not (repo / "docs" / "agent-logs").exists()


def test_append_rejects_non_json(repo):
    run_cli(repo, "append", "--record", "not json at all")
    assert not (repo / ".openup" / "run-log-pending.jsonl").exists()


# --- flush ----------------------------------------------------------------


def test_flush_drains_into_lane_shard_stages_it_and_empties_queue(repo):
    run_cli(repo, "append", "--record", json.dumps(record("aaa")))
    out = run_cli(repo, "flush", "--worktree", str(repo))

    target = shard(repo, "2026-07-27-T-140.jsonl")
    assert target.exists()
    assert json.loads(target.read_text().strip())["sha"] == "aaa"
    assert out.stdout.strip() == "docs/agent-logs/runs/2026-07-27-T-140.jsonl"
    assert (repo / ".openup" / "run-log-pending.jsonl").read_text().strip() == ""

    staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=repo,
                            capture_output=True, text=True).stdout
    assert "docs/agent-logs/runs/2026-07-27-T-140.jsonl" in staged


def test_flush_routes_each_record_to_its_own_lane_shard(repo):
    run_cli(repo, "append", "--record", json.dumps(record("aaa", task_id="T-140")))
    run_cli(repo, "append", "--record", json.dumps(record("bbb", task_id="T-147")))
    run_cli(repo, "flush", "--worktree", str(repo))

    assert json.loads(shard(repo, "2026-07-27-T-140.jsonl").read_text())["sha"] == "aaa"
    assert json.loads(shard(repo, "2026-07-27-T-147.jsonl").read_text())["sha"] == "bbb"


def test_flush_dedupes_a_sha_already_in_the_shard(repo):
    target = shard(repo, "2026-07-27-T-140.jsonl")
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(record("aaa")) + "\n")

    run_cli(repo, "append", "--record", json.dumps(record("aaa")))
    run_cli(repo, "flush", "--worktree", str(repo))

    assert len(target.read_text().strip().splitlines()) == 1
    assert (repo / ".openup" / "run-log-pending.jsonl").read_text().strip() == ""


def test_flush_dedupes_within_one_batch(repo):
    run_cli(repo, "append", "--record", json.dumps(record("aaa")))
    run_cli(repo, "append", "--record", json.dumps(record("aaa")))
    run_cli(repo, "flush", "--worktree", str(repo))

    assert len(shard(repo, "2026-07-27-T-140.jsonl").read_text().strip().splitlines()) == 1


def test_flush_tolerates_corrupt_lines_and_keeps_the_good_ones(repo):
    pending = repo / ".openup" / "run-log-pending.jsonl"
    pending.parent.mkdir(parents=True)
    pending.write_text("{not json\n" + json.dumps(record("aaa")) + "\n\n")

    res = run_cli(repo, "flush", "--worktree", str(repo))

    assert res.returncode == 0
    assert json.loads(shard(repo, "2026-07-27-T-140.jsonl").read_text())["sha"] == "aaa"


def test_flush_on_missing_or_empty_queue_is_a_silent_noop(repo):
    res = run_cli(repo, "flush", "--worktree", str(repo))
    assert res.returncode == 0 and res.stdout.strip() == ""
    assert not (repo / "docs" / "agent-logs").exists()


def test_flush_uses_branch_when_task_id_is_absent(repo):
    run_cli(repo, "append",
            "--record", json.dumps(record("aaa", task_id=None, branch="feat/x")))
    run_cli(repo, "flush", "--worktree", str(repo))
    assert shard(repo, "2026-07-27-feat-x.jsonl").exists()


# --- pathspec guard -------------------------------------------------------


@pytest.mark.parametrize("command", [
    'git commit -m "msg" -- scripts/foo.py',
    "git commit scripts/foo.py",
    'cd /tmp/wt && git commit -m "msg" docs/a.md',
])
def test_pathspec_limited_commits_are_detected(command):
    assert runlog.commit_has_pathspec(command) is True


@pytest.mark.parametrize("command", [
    'git commit -m "msg"',
    'git commit -am "msg"',
    'git commit -a -m "msg"',
    'git commit --message="msg"',
    'git commit --message "msg"',
    "git commit --amend --no-edit",
    'cd /tmp/wt && git commit -q -m "msg"',
    'git commit -m "a -- b"',
])
def test_unrestricted_commits_are_not_treated_as_pathspec(command):
    assert runlog.commit_has_pathspec(command) is False


def test_flush_skips_entirely_on_a_pathspec_limited_commit(repo):
    run_cli(repo, "append", "--record", json.dumps(record("aaa")))
    run_cli(repo, "flush", "--worktree", str(repo),
            "--command", 'git commit -m "x" -- scripts/foo.py')

    pending = repo / ".openup" / "run-log-pending.jsonl"
    assert len(pending.read_text().strip().splitlines()) == 1   # queue intact
    assert not (repo / "docs" / "agent-logs").exists()          # nothing staged


def test_flush_proceeds_on_an_unrestricted_commit_command(repo):
    run_cli(repo, "append", "--record", json.dumps(record("aaa")))
    run_cli(repo, "flush", "--worktree", str(repo),
            "--command", 'git commit -m "x"')
    assert shard(repo, "2026-07-27-T-140.jsonl").exists()


# --- fail-open ------------------------------------------------------------


def test_every_subcommand_exits_zero_even_outside_a_git_repo(tmp_path):
    for args in (["append", "--record", "{}"], ["flush"], ["path"]):
        res = subprocess.run(
            ["python3", str(SCRIPT), "--cwd", str(tmp_path), *args],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert res.returncode == 0, (args, res.stderr)


def test_flush_exits_zero_when_the_queue_is_unreadable(repo):
    pending = repo / ".openup" / "run-log-pending.jsonl"
    pending.parent.mkdir(parents=True)
    pending.write_text(json.dumps(record("aaa")) + "\n")
    pending.chmod(0o000)
    try:
        res = run_cli(repo, "flush", "--worktree", str(repo))
        assert res.returncode == 0
    finally:
        pending.chmod(0o644)
