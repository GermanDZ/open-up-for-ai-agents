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
HOOKS_DIR = REPO_ROOT / ".claude" / "scripts" / "hooks"
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
        log = self.repo.dir / "docs" / "agent-logs" / "agent-runs.jsonl"
        self.assertTrue(log.exists())
        lines = [l for l in log.read_text().splitlines() if l.strip()]
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["event"], "commit")
        self.assertEqual(rec["task_id"], "T-006")
        self.assertEqual(rec["model"], "claude-opus-test")
        _, sha = git(self.repo.dir, "rev-parse", "HEAD").stdout, None
        self.assertEqual(rec["sha"],
                         git(self.repo.dir, "rev-parse", "HEAD").stdout.strip())
        # Gate flipped.
        g = state_cli(self.repo.state_dir, "get", "gates.log_written")
        self.assertEqual(g.stdout.strip(), "true")

    def test_idempotent_same_sha(self):
        self._make_commit()
        run_hook("auto-log-commit.py", self._commit_payload(), self.repo.dir)
        run_hook("auto-log-commit.py", self._commit_payload(), self.repo.dir)
        log = self.repo.dir / "docs" / "agent-logs" / "agent-runs.jsonl"
        lines = [l for l in log.read_text().splitlines() if l.strip()]
        self.assertEqual(len(lines), 1)  # not double-appended

    def test_new_commit_appends_again(self):
        self._make_commit()
        run_hook("auto-log-commit.py", self._commit_payload(), self.repo.dir)
        # second distinct commit
        (self.repo.dir / "g.txt").write_text("y\n")
        git(self.repo.dir, "add", "-A")
        git(self.repo.dir, "commit", "-q", "-m", "feat: more [T-006]")
        run_hook("auto-log-commit.py", self._commit_payload(), self.repo.dir)
        log = self.repo.dir / "docs" / "agent-logs" / "agent-runs.jsonl"
        lines = [l for l in log.read_text().splitlines() if l.strip()]
        self.assertEqual(len(lines), 2)

    def test_non_commit_bash_ignored(self):
        payload = {"tool_name": "Bash", "cwd": str(self.repo.dir),
                   "tool_input": {"command": "git status"}}
        run_hook("auto-log-commit.py", payload, self.repo.dir)
        log = self.repo.dir / "docs" / "agent-logs" / "agent-runs.jsonl"
        self.assertFalse(log.exists())


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
        self.assertRegex(rm, r"\|\s*T-006\s*\|[^|]*\|\s*completed\s*\|")
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
