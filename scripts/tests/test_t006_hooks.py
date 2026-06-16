#!/usr/bin/env python3
"""Unit tests for the T-006 blocking-gate hooks + sync-status generator.

Run with either:
    python3 -m unittest scripts.tests.test_t006_hooks
    python3 scripts/tests/test_t006_hooks.py

Each test builds an isolated temp git repo and an isolated .openup state dir
so nothing touches the live project. Hooks are driven exactly as the harness
drives them: a JSON payload on stdin, behavior asserted via exit code +
stderr. ``--state-dir`` points the state CLI at the temp dir; the hooks
themselves resolve state via ``scripts/openup-state.py`` inside the temp repo,
so each temp repo gets its own copy of the scripts under ``scripts/``.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / "docs-eng-process" / ".claude-templates" / "scripts" / "hooks"
SCRIPTS_DIR = REPO_ROOT / "scripts"

STATE_CLI = SCRIPTS_DIR / "openup-state.py"
SCHEMA = SCRIPTS_DIR / "openup-state.schema.json"
SYNC_STATUS = SCRIPTS_DIR / "sync-status.py"


def git(cwd, *args):
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True
    )


def state_cli(state_dir, *args, cwd=None):
    cmd = [sys.executable, str(STATE_CLI), *args, "--state-dir", str(state_dir)]
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def run_hook(hook_name, payload, cwd):
    """Invoke a hook with a JSON payload on stdin; return CompletedProcess."""
    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / hook_name)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return proc


def shard_lines(repo_dir, task_id=None):
    """All JSONL records across the lane-owned run shards (T-046). Filter to one
    lane with task_id (matches the `<date>-<task_id>.jsonl` filename suffix)."""
    runs = Path(repo_dir) / "docs" / "agent-logs" / "runs"
    if not runs.is_dir():
        return []
    out = []
    for shard in sorted(runs.glob("*.jsonl")):
        if task_id and not shard.name.endswith(f"-{task_id}.jsonl"):
            continue
        out += [l for l in shard.read_text().splitlines() if l.strip()]
    return out


def shard_files(repo_dir):
    runs = Path(repo_dir) / "docs" / "agent-logs" / "runs"
    return sorted(runs.glob("*.jsonl")) if runs.is_dir() else []


class TempRepo:
    """A throwaway git repo with a project-local copy of scripts/."""

    def __init__(self):
        self.dir = Path(tempfile.mkdtemp())
        # State dir lives inside the repo at .openup so hooks find it.
        self.state_dir = self.dir / ".openup"
        # Mirror scripts/ so hooks can call scripts/openup-state.py inside cwd.
        (self.dir / "scripts").mkdir(parents=True, exist_ok=True)
        shutil.copy(STATE_CLI, self.dir / "scripts" / "openup-state.py")
        shutil.copy(SCHEMA, self.dir / "scripts" / "openup-state.schema.json")
        shutil.copy(SYNC_STATUS, self.dir / "scripts" / "sync-status.py")
        git(self.dir, "init", "-q")
        git(self.dir, "config", "user.email", "t@example.com")
        git(self.dir, "config", "user.name", "Tester")
        # Hermetic: never depend on the host's commit-signing setup. Without
        # this, a host with commit.gpgsign=true makes every test commit fail
        # ("failed to write commit object") and the hooks have nothing to log.
        git(self.dir, "config", "commit.gpgsign", "false")
        git(self.dir, "checkout", "-q", "-b", "main")
        # Mirror production: .openup is runtime state, gitignored.
        (self.dir / ".gitignore").write_text(".openup/\n")
        (self.dir / "README.md").write_text("seed\n")
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-q", "-m", "seed")

    def init_state(self, track="standard", plan=None, task_id="T-006"):
        args = [
            "init",
            "--task-id", task_id,
            "--iteration", "3",
            "--phase", "construction",
            "--track", track,
            "--branch", "feature/T-006-blocking-gates",
            "--worktree", str(self.dir),
            "--force",
        ]
        if plan:
            args += ["--plan", plan]
        return state_cli(self.state_dir, *args)

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


# --------------------------------------------------------------------------
# gate-edits.py
# --------------------------------------------------------------------------
class GateEditsTests(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()

    def tearDown(self):
        self.repo.cleanup()

    def _edit_payload(self, path):
        return {
            "tool_name": "Edit",
            "cwd": str(self.repo.dir),
            "tool_input": {"file_path": path},
        }

    def test_blocks_source_without_state(self):
        # No state at all → source edit blocked.
        proc = run_hook("gate-edits.py",
                        self._edit_payload("src/app.py"), self.repo.dir)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("gate-edits", proc.stderr)

    def test_blocks_source_without_plan_gate(self):
        self.repo.init_state(track="standard")  # plan_persisted = false
        proc = run_hook("gate-edits.py",
                        self._edit_payload("src/app.py"), self.repo.dir)
        self.assertEqual(proc.returncode, 2)

    def test_allows_source_with_plan_gate(self):
        self.repo.init_state(track="standard", plan="docs/changes/T-006/plan.md")
        proc = run_hook("gate-edits.py",
                        self._edit_payload("src/app.py"), self.repo.dir)
        self.assertEqual(proc.returncode, 0)

    def test_allows_exempt_paths(self):
        # No state, but exempt paths must always be allowed.
        for p in (
            "docs/explorations/notes.md",
            ".openup/scratch.json",
            ".claude/memory/iteration-learnings.md",
            "docs/agent-logs/agent-runs.jsonl",
        ):
            proc = run_hook("gate-edits.py",
                            self._edit_payload(p), self.repo.dir)
            self.assertEqual(proc.returncode, 0, f"{p} should be exempt")

    def test_allows_derived_project_status_without_state(self):
        # Regression: docs/project-status.md is a fully-derived view written by
        # sync-status.py + /openup-retrospective step 7. Gating it blocked the
        # retrospective's own status update. It must be exempt even with no state.
        proc = run_hook("gate-edits.py",
                        self._edit_payload("docs/project-status.md"), self.repo.dir)
        self.assertEqual(proc.returncode, 0)

    def test_allows_path_outside_repo_without_state(self):
        # Regression: the harness memory dir lives at
        # ~/.claude/projects/<id>/memory/ — outside the repo. A repo-scoped
        # iteration gate must never fire on a path it doesn't own.
        payload = {
            "tool_name": "Write",
            "cwd": str(self.repo.dir),
            "tool_input": {
                "file_path": "/Users/x/.claude/projects/abc/memory/note.md"},
        }
        proc = run_hook("gate-edits.py", payload, self.repo.dir)
        self.assertEqual(proc.returncode, 0)

    def test_allows_quick_track_without_plan(self):
        self.repo.init_state(track="quick")  # plan_persisted = false
        proc = run_hook("gate-edits.py",
                        self._edit_payload("src/app.py"), self.repo.dir)
        self.assertEqual(proc.returncode, 0)
        # Bypass should be audited.
        log = self.repo.dir / ".claude" / "memory" / "bypass-log.md"
        self.assertTrue(log.exists())
        self.assertIn("quick-track", log.read_text())

    def test_notebook_path_resolved(self):
        self.repo.init_state(track="standard")  # no plan → block
        payload = {
            "tool_name": "NotebookEdit",
            "cwd": str(self.repo.dir),
            "tool_input": {"notebook_path": "src/analysis.ipynb"},
        }
        proc = run_hook("gate-edits.py", payload, self.repo.dir)
        self.assertEqual(proc.returncode, 2)

    def test_ignores_non_edit_tool(self):
        payload = {"tool_name": "Bash", "cwd": str(self.repo.dir),
                   "tool_input": {"command": "ls"}}
        proc = run_hook("gate-edits.py", payload, self.repo.dir)
        self.assertEqual(proc.returncode, 0)

    def test_plan_mode_path_exempt_without_state(self):
        # T-041 Fix 8: plan-mode plan files (…/.claude/plans/) are process
        # state — allowed even with no active iteration, even outside the repo.
        payload = {
            "tool_name": "Write",
            "cwd": str(self.repo.dir),
            "tool_input": {"file_path": "/Users/x/.claude/plans/foo.md"},
        }
        proc = run_hook("gate-edits.py", payload, self.repo.dir)
        self.assertEqual(proc.returncode, 0)

    def test_worktree_state_resolved_from_target(self):
        # T-041 Fix 7: state is read from the worktree that owns the edit, not
        # the harness cwd. Here cwd (main repo) has NO state, but the linked
        # worktree DOES (with a plan) — an edit inside the worktree is allowed.
        wt = self.repo.dir.parent / (self.repo.dir.name + "-wt")
        try:
            git(self.repo.dir, "worktree", "add", "-q", str(wt),
                "-b", "feature/wt")
            # Mirror scripts/ + init standard state WITH a plan inside the wt.
            (wt / "scripts").mkdir(parents=True, exist_ok=True)
            shutil.copy(STATE_CLI, wt / "scripts" / "openup-state.py")
            shutil.copy(SCHEMA, wt / "scripts" / "openup-state.schema.json")
            state_cli(wt / ".openup", "init", "--task-id", "T-007",
                      "--iteration", "1", "--phase", "construction",
                      "--track", "standard", "--branch", "feature/wt",
                      "--worktree", str(wt), "--plan",
                      "docs/changes/T-007/plan.md", "--force")
            # cwd is the MAIN repo (no state); target is INSIDE the worktree.
            payload = {
                "tool_name": "Edit",
                "cwd": str(self.repo.dir),
                "tool_input": {"file_path": str(wt / "src" / "app.py")},
            }
            proc = run_hook("gate-edits.py", payload, self.repo.dir)
            self.assertEqual(proc.returncode, 0, proc.stderr)
        finally:
            git(self.repo.dir, "worktree", "remove", "--force", str(wt))


# --------------------------------------------------------------------------
# auto-log-commit.py
# --------------------------------------------------------------------------
class AutoLogCommitTests(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()
        self.repo.init_state(track="standard", plan="docs/changes/T-006/plan.md")

    def tearDown(self):
        self.repo.cleanup()

    def _make_commit(self):
        (self.repo.dir / "f.txt").write_text("x\n")
        git(self.repo.dir, "add", "-A")
        git(self.repo.dir, "commit", "-q", "-m", "feat: change [T-006]")

    def _commit_payload(self):
        return {
            "tool_name": "Bash",
            "cwd": str(self.repo.dir),
            "tool_input": {"command": 'git commit -m "feat: change [T-006]"'},
            "tool_response": {"stdout": "1 file changed", "returncode": 0},
            "model": "claude-opus-test",
        }

    def test_appends_once_and_sets_gate(self):
        self._make_commit()
        proc = run_hook("auto-log-commit.py", self._commit_payload(),
                        self.repo.dir)
        self.assertEqual(proc.returncode, 0)
        # T-046: record lands in the lane shard, NOT the shared agent-runs.jsonl.
        self.assertFalse(
            (self.repo.dir / "docs" / "agent-logs" / "agent-runs.jsonl").exists())
        lines = shard_lines(self.repo.dir, "T-006")
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["event"], "commit")
        self.assertEqual(rec["task_id"], "T-006")
        self.assertEqual(rec["model"], "claude-opus-test")
        self.assertEqual(rec["sha"],
                         git(self.repo.dir, "rev-parse", "HEAD").stdout.strip())
        # Gate flipped.
        g = state_cli(self.repo.state_dir, "get", "gates.log_written")
        self.assertEqual(g.stdout.strip(), "true")

    def test_resolves_task_from_worktree_when_cwd_has_no_state(self):
        # T-042 Fix-7b: cwd (main) has no state; a linked worktree does → the
        # commit record carries the worktree's task_id, not null.
        repo = TempRepo()  # fresh: scripts present, NO init_state on main
        wt = repo.dir.parent / (repo.dir.name + "-alc-wt")
        try:
            git(repo.dir, "worktree", "add", "-q", str(wt), "-b", "feature/alc")
            (wt / "scripts").mkdir(parents=True, exist_ok=True)
            shutil.copy(STATE_CLI, wt / "scripts" / "openup-state.py")
            shutil.copy(SCHEMA, wt / "scripts" / "openup-state.schema.json")
            state_cli(wt / ".openup", "init", "--task-id", "T-077",
                      "--iteration", "1", "--phase", "construction",
                      "--track", "standard", "--branch", "feature/alc",
                      "--worktree", str(wt), "--force")
            # Commit in MAIN (the pinned cwd) while state lives in the worktree.
            (repo.dir / "f.txt").write_text("x\n")
            git(repo.dir, "add", "-A")
            git(repo.dir, "commit", "-q", "-m", "feat: change [T-077]")
            payload = {
                "tool_name": "Bash", "cwd": str(repo.dir),
                "tool_input": {"command": 'git commit -m "feat: change [T-077]"'},
                "tool_response": {"stdout": "1 file changed", "returncode": 0},
            }
            proc = run_hook("auto-log-commit.py", payload, repo.dir)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            rec = json.loads(shard_lines(repo.dir, "T-077")[-1])
            self.assertEqual(rec.get("task_id"), "T-077")  # not null
        finally:
            git(repo.dir, "worktree", "remove", "--force", str(wt))
            repo.cleanup()

    def test_idempotent_same_sha(self):
        self._make_commit()
        run_hook("auto-log-commit.py", self._commit_payload(), self.repo.dir)
        run_hook("auto-log-commit.py", self._commit_payload(), self.repo.dir)
        self.assertEqual(len(shard_lines(self.repo.dir, "T-006")), 1)  # not double

    def test_new_commit_appends_again(self):
        self._make_commit()
        run_hook("auto-log-commit.py", self._commit_payload(), self.repo.dir)
        # second distinct commit
        (self.repo.dir / "g.txt").write_text("y\n")
        git(self.repo.dir, "add", "-A")
        git(self.repo.dir, "commit", "-q", "-m", "feat: more [T-006]")
        run_hook("auto-log-commit.py", self._commit_payload(), self.repo.dir)
        # Same task + same UTC day → same shard, two records.
        self.assertEqual(len(shard_lines(self.repo.dir, "T-006")), 2)

    def test_non_commit_bash_ignored(self):
        payload = {"tool_name": "Bash", "cwd": str(self.repo.dir),
                   "tool_input": {"command": "git status"}}
        run_hook("auto-log-commit.py", payload, self.repo.dir)
        self.assertEqual(shard_files(self.repo.dir), [])  # no shard created

    def test_two_lanes_write_disjoint_shards(self):
        # R2 invariant: distinct task_ids → distinct shard files, so a merge of
        # two branches touches disjoint paths and cannot conflict.
        ld = self.repo.dir / "docs" / "agent-logs"
        for tid in ("T-043", "T-044"):
            subprocess.run(
                [sys.executable, str(STATE_CLI), "log-event", "--event", "x",
                 "--task-id", tid, "--branch", f"feature/{tid}",
                 "--log-dir", str(ld)],
                capture_output=True, text=True, check=True)
        names = {p.name.split("-", 3)[-1] for p in shard_files(self.repo.dir)}
        self.assertEqual(names, {"T-043.jsonl", "T-044.jsonl"})
        # runs build consolidates both, ts-ordered.
        subprocess.run(
            [sys.executable, str(STATE_CLI), "runs", "build",
             "--log-dir", str(ld)], capture_output=True, text=True, check=True)
        built = (ld / "agent-runs.jsonl").read_text().splitlines()
        self.assertEqual(len([l for l in built if l.strip()]), 2)

    def test_skips_log_only_commit(self):
        # A commit that touched ONLY the run log is pure bookkeeping. Logging
        # it again would re-dirty the log and tail-chase forever — the hook
        # must skip it so a final "commit the log" reaches a clean tree.
        self._make_commit()  # a real prior commit (gives the next one a parent)
        log = self.repo.dir / "docs" / "agent-logs" / "agent-runs.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text('{"event":"commit","sha":"abc","task_id":"T-006"}\n')
        git(self.repo.dir, "add", "-A")
        git(self.repo.dir, "commit", "-q", "-m", "chore(logs): record [T-006]")
        before = log.read_text()
        proc = run_hook("auto-log-commit.py", self._commit_payload(),
                        self.repo.dir)
        self.assertEqual(proc.returncode, 0)
        # No new record appended — the log-only commit was recognized.
        self.assertEqual(log.read_text(), before)

    def test_skips_logs_dir_only_commit(self):
        # T-012 regression: the complete-task closing commit bundles the
        # markdown traceability log WITH agent-runs.jsonl — both under
        # docs/agent-logs/. That is still pure bookkeeping, so the hook must
        # skip it; otherwise it appends a fresh record and leaves the JSONL
        # dirty every iteration (the "always uncommitted after PR" bug).
        self._make_commit()  # prior commit → gives the next one a parent
        logdir = self.repo.dir / "docs" / "agent-logs"
        logdir.mkdir(parents=True, exist_ok=True)
        jsonl = logdir / "agent-runs.jsonl"
        jsonl.write_text('{"event":"commit","sha":"abc","task_id":"T-006"}\n')
        md = logdir / "2026" / "06" / "11" / "run.md"
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text("# run log\n")
        git(self.repo.dir, "add", "-A")
        git(self.repo.dir, "commit", "-q", "-m", "docs(logs): traceability [T-006]")
        before = jsonl.read_text()
        proc = run_hook("auto-log-commit.py", self._commit_payload(),
                        self.repo.dir)
        self.assertEqual(proc.returncode, 0)
        # Markdown-log + JSONL bundled together is recognized as logs-only.
        self.assertEqual(jsonl.read_text(), before)

    def test_logs_commit_with_code_still_appended(self):
        # Negative control: a commit touching a code file ALONGSIDE log files
        # is NOT logs-only, so it must still be logged — the broadened guard
        # must not over-skip real work.
        self._make_commit()
        run_hook("auto-log-commit.py", self._commit_payload(), self.repo.dir)
        n_before = len(shard_lines(self.repo.dir, "T-006"))
        (self.repo.dir / "h.txt").write_text("z\n")
        note = self.repo.dir / "docs" / "agent-logs" / "note.md"
        note.write_text("n\n")
        git(self.repo.dir, "add", "-A")
        git(self.repo.dir, "commit", "-q", "-m", "feat: mix code and log [T-006]")
        run_hook("auto-log-commit.py", self._commit_payload(), self.repo.dir)
        n_after = len(shard_lines(self.repo.dir, "T-006"))
        self.assertEqual(n_after, n_before + 1)


# --------------------------------------------------------------------------
# validate-commit.py
# --------------------------------------------------------------------------
class ValidateCommitTests(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()

    def tearDown(self):
        self.repo.cleanup()

    def _payload(self, msg):
        return {
            "tool_name": "Bash",
            "cwd": str(self.repo.dir),
            "tool_input": {"command": f'git commit -m "{msg}"'},
        }

    def test_rejects_missing_tag_when_state_has_task_id(self):
        self.repo.init_state(task_id="T-006")
        proc = run_hook("validate-commit.py",
                        self._payload("feat: add thing"), self.repo.dir)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("T-006", proc.stderr)

    def test_accepts_with_tag_when_state_has_task_id(self):
        self.repo.init_state(task_id="T-006")
        proc = run_hook("validate-commit.py",
                        self._payload("feat: add thing [T-006]"), self.repo.dir)
        self.assertEqual(proc.returncode, 0)

    def test_optional_tag_without_state(self):
        # No state → tag stays optional, well-formed message allowed.
        proc = run_hook("validate-commit.py",
                        self._payload("feat: add thing"), self.repo.dir)
        self.assertEqual(proc.returncode, 0)

    def test_malformed_still_rejected(self):
        self.repo.init_state(task_id="T-006")
        proc = run_hook("validate-commit.py",
                        self._payload("nonsense message"), self.repo.dir)
        self.assertEqual(proc.returncode, 2)

    def test_openup_skip_bypasses(self):
        self.repo.init_state(task_id="T-006")
        proc = run_hook("validate-commit.py",
                        self._payload("wip stuff [openup-skip]"), self.repo.dir)
        self.assertEqual(proc.returncode, 0)
        log = self.repo.dir / ".claude" / "memory" / "bypass-log.md"
        self.assertTrue(log.exists())


# --------------------------------------------------------------------------
# on-stop.py
# --------------------------------------------------------------------------
class OnStopTests(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()
        self.repo.init_state(track="standard", plan="docs/changes/T-006/plan.md")

    def tearDown(self):
        self.repo.cleanup()

    def _stop_payload(self):
        return {"cwd": str(self.repo.dir)}

    def _commit_on_branch(self):
        git(self.repo.dir, "checkout", "-q", "-b",
            "feature/T-006-blocking-gates")
        (self.repo.dir / "f.txt").write_text("x\n")
        git(self.repo.dir, "add", "-A")
        git(self.repo.dir, "commit", "-q", "-m", "feat: change [T-006]")

    def test_blocks_when_commits_but_log_not_written(self):
        self._commit_on_branch()
        proc = run_hook("on-stop.py", self._stop_payload(), self.repo.dir)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("log_written", proc.stderr)

    def test_allows_when_log_written(self):
        self._commit_on_branch()
        state_cli(self.repo.state_dir, "set-gate", "log_written", "true")
        state_cli(self.repo.state_dir, "set-gate", "roadmap_synced", "true")
        proc = run_hook("on-stop.py", self._stop_payload(), self.repo.dir)
        self.assertEqual(proc.returncode, 0)

    def test_blocks_dirty_worktree(self):
        (self.repo.dir / "dirty.txt").write_text("z\n")
        proc = run_hook("on-stop.py", self._stop_payload(), self.repo.dir)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("UNCOMMITTED", proc.stderr)

    def test_exempt_log_dirty_does_not_block(self):
        # T-046: the lane shards under docs/agent-logs/runs/ lag HEAD by one
        # append by design. With gates satisfied and ONLY a shard dirty, on-stop
        # must allow stop (and sweep it).
        self._commit_on_branch()
        state_cli(self.repo.state_dir, "set-gate", "log_written", "true")
        state_cli(self.repo.state_dir, "set-gate", "roadmap_synced", "true")
        shard = (self.repo.dir / "docs" / "agent-logs" / "runs"
                 / "2026-06-16-T-006.jsonl")
        shard.parent.mkdir(parents=True, exist_ok=True)
        shard.write_text('{"event":"commit"}\n')
        git(self.repo.dir, "add", "-A")
        git(self.repo.dir, "commit", "-q", "-m", "chore: track shard [T-006]")
        # Re-dirty it the way auto-log-commit does (append after the commit).
        with shard.open("a") as fh:
            fh.write('{"event":"commit","sha":"deadbeef"}\n')
        st = git(self.repo.dir, "status", "--porcelain").stdout.strip()
        self.assertIn("docs/agent-logs/runs/", st)
        proc = run_hook("on-stop.py", self._stop_payload(), self.repo.dir)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_non_exempt_dirty_still_blocks(self):
        # A dirty non-exempt file alongside the exempt shard must still block.
        self._commit_on_branch()
        state_cli(self.repo.state_dir, "set-gate", "log_written", "true")
        state_cli(self.repo.state_dir, "set-gate", "roadmap_synced", "true")
        shard = (self.repo.dir / "docs" / "agent-logs" / "runs"
                 / "2026-06-16-T-006.jsonl")
        shard.parent.mkdir(parents=True, exist_ok=True)
        shard.write_text('{"event":"commit"}\n')
        (self.repo.dir / "scripts" / "foo.py").write_text("print('x')\n")
        proc = run_hook("on-stop.py", self._stop_payload(), self.repo.dir)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("UNCOMMITTED", proc.stderr)
        self.assertIn("foo.py", proc.stderr)

    def test_blocks_when_log_gate_key_absent(self):
        # Defense-in-depth: a malformed state missing the log_written gate key
        # must be treated as UNMET (block), not skipped. Hand-corrupt the file
        # to delete the key (unreachable via the sanctioned init, which seeds
        # all five gates, but exactly the failure class T-006 eliminates).
        self._commit_on_branch()
        sp = self.repo.state_dir / "state.json"
        data = json.loads(sp.read_text())
        del data["gates"]["log_written"]
        sp.write_text(json.dumps(data))
        proc = run_hook("on-stop.py", self._stop_payload(), self.repo.dir)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("log_written", proc.stderr)


# --------------------------------------------------------------------------
# sync-status.py
# --------------------------------------------------------------------------
class SyncStatusTests(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()
        self.repo.init_state(track="standard", plan="docs/changes/T-006/plan.md")
        docs = self.repo.dir / "docs"
        docs.mkdir(exist_ok=True)
        self.roadmap = docs / "roadmap.md"
        self.ps = docs / "project-status.md"
        self.roadmap.write_text(
            "# Roadmap\n\n"
            "| ID | Title | Status | Priority | Depends on |\n"
            "|---|---|---|---|---|\n"
            "| T-005 | State file | completed (2026-06-10) | high | — |\n"
            "| T-006 | Blocking gates | planned | high | T-005 |\n"
        )
        self.ps.write_text(
            "# Project Status\n\n"
            "**Phase**: construction\n"
            "**Iteration**: 1\n"
            "**Iteration Goal**: old goal\n"
            "**Status**: planned\n"
            "**Current Task**: T-000\n"
            "**Last Updated**: 2026-01-01\n"
            "**Updated By**: hand\n"
        )

    def tearDown(self):
        self.repo.cleanup()

    def _run_sync(self):
        cmd = [
            sys.executable, str(SYNC_STATUS),
            "--state-dir", str(self.repo.state_dir),
            "--roadmap", str(self.roadmap),
            "--project-status", str(self.ps),
            # Isolate from the live repo's docs/status-notes/ (T-024).
            "--notes-dir", str(self.repo.dir / "no-status-notes"),
        ]
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_in_progress_sync(self):
        proc = self._run_sync()
        self.assertEqual(proc.returncode, 0)
        rm = self.roadmap.read_text()
        # T-006 row flipped to in-progress; T-005 untouched.
        self.assertRegex(rm, r"\|\s*T-006\s*\|[^|]*\|\s*in-progress\s*\|")
        self.assertIn("completed (2026-06-10)", rm)  # T-005 preserved
        ps = self.ps.read_text()
        self.assertIn("**Current Task**: T-006", ps)
        self.assertIn("**Status**: in-progress", ps)
        self.assertIn("**Iteration**: 3", ps)
        self.assertIn("**Iteration Goal**: T-006 — Blocking gates", ps)
        self.assertIn("**Updated By**: sync-status.py", ps)
        # roadmap_synced gate flipped.
        g = state_cli(self.repo.state_dir, "get", "gates.roadmap_synced")
        self.assertEqual(g.stdout.strip(), "true")

    def test_completed_when_all_gates_met(self):
        for gate in ("team_deployed", "log_written", "roadmap_synced"):
            state_cli(self.repo.state_dir, "set-gate", gate, "true")
        proc = self._run_sync()
        self.assertEqual(proc.returncode, 0)
        rm = self.roadmap.read_text()
        # completed cells are date-stamped to match the roadmap convention (T-024)
        self.assertRegex(
            rm, r"\|\s*T-006\s*\|[^|]*\|\s*completed \(\d{4}-\d{2}-\d{2}\)\s*\|"
        )
        self.assertIn("**Status**: completed", self.ps.read_text())

    def test_idempotent(self):
        self._run_sync()
        rm1 = self.roadmap.read_text()
        ps1 = self.ps.read_text()
        self._run_sync()
        # Status/goal stable; only Last Updated date is regenerated (same day).
        self.assertEqual(self.roadmap.read_text(), rm1)
        self.assertEqual(self.ps.read_text(), ps1)

    def test_no_state(self):
        empty = self.repo.dir / "empty-state"
        cmd = [
            sys.executable, str(SYNC_STATUS),
            "--state-dir", str(empty),
            "--roadmap", str(self.roadmap),
            "--project-status", str(self.ps),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 3)


if __name__ == "__main__":
    unittest.main()
