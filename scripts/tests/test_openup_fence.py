#!/usr/bin/env python3
"""Unit tests for scripts/openup-fence.py (T-024).

Run with either:
    python3 -m unittest scripts.tests.test_openup_fence
    python3 scripts/tests/test_openup_fence.py

Hermetic: each test builds an isolated fixture git repo (a `main` trunk and a
lane branch with its own plan frontmatter), an injected --claims-dir, and an
injected --state-dir, so it never depends on the live repo, real leases, or
the live trunk. The fence is exercised through its CLI exactly as the
pre-push hook and /openup-complete-task do.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "openup-fence.py"

OK, USAGE, NO_TASK, VIOLATION = 0, 2, 3, 8

TASK = "T-100"


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


class FenceRepo:
    """Throwaway repo: main trunk + lane branch for TASK with frontmatter."""

    def __init__(self, touches=("src/widget.py",)):
        self.dir = Path(tempfile.mkdtemp())
        # Overrides live OUTSIDE the repo so `git add -A` never sees them.
        self.aux = Path(tempfile.mkdtemp())
        self.claims = self.aux / "claims-override"
        self.state = self.aux / "state-override"
        git(self.dir, "init", "-q")
        git(self.dir, "config", "user.email", "t@example.com")
        git(self.dir, "config", "user.name", "Tester")
        git(self.dir, "config", "commit.gpgsign", "false")
        git(self.dir, "checkout", "-q", "-b", "main")
        plan = self.dir / "docs" / "changes" / TASK
        plan.mkdir(parents=True)
        fm = "\n".join(
            ["---", f"id: {TASK}", "title: Fence fixture", "status: in-progress",
             "priority: medium", "depends-on: []",
             "touches: [%s]" % ", ".join(touches), "---", "", f"# {TASK}", ""]
        )
        (plan / "plan.md").write_text(fm, encoding="utf-8")
        (self.dir / "src").mkdir()
        (self.dir / "src" / "widget.py").write_text("x = 1\n")
        (self.dir / "src" / "other.py").write_text("y = 1\n")
        (self.dir / "docs" / "roadmap.md").write_text("# Roadmap\n")
        (self.dir / "docs" / "project-status.md").write_text("# Status\n")
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-q", "-m", "seed")
        git(self.dir, "checkout", "-q", "-b", f"lane/{TASK}")

    def commit(self, relpath, content="changed\n", msg="lane edit"):
        p = self.dir / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-q", "-m", msg)

    def advance_main(self):
        """Move main ahead so it is no longer an ancestor of the lane."""
        git(self.dir, "checkout", "-q", "main")
        (self.dir / "TRUNK.md").write_text("moved\n")
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-q", "-m", "trunk moves")
        git(self.dir, "checkout", "-q", f"lane/{TASK}")

    def write_state(self, task_id=TASK):
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / "state.json").write_text(
            json.dumps({"task_id": task_id}), encoding="utf-8"
        )

    def write_claim(self, touches, task_id=TASK):
        self.claims.mkdir(parents=True, exist_ok=True)
        (self.claims / f"{task_id}.json").write_text(
            json.dumps({"task_id": task_id, "session_id": "S1",
                        "touches": list(touches)}),
            encoding="utf-8",
        )

    def fence(self, *args, sub="check"):
        cmd = [sys.executable, str(SCRIPT), sub, "--base", "main",
               "--claims-dir", str(self.claims),
               "--state-dir", str(self.state), *args]
        return subprocess.run(cmd, cwd=self.dir, capture_output=True, text=True)

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        shutil.rmtree(self.aux, ignore_errors=True)


class FenceCheckTests(unittest.TestCase):
    def setUp(self):
        self.repo = FenceRepo()

    def tearDown(self):
        self.repo.cleanup()

    def test_in_lane_touches_and_change_folder_pass(self):
        self.repo.commit("src/widget.py")
        self.repo.commit(f"docs/changes/{TASK}/design.md", "decision\n")
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_out_of_lane_blocks_and_names_file(self):
        self.repo.commit("src/other.py")
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, VIOLATION)
        self.assertIn("OUT OF LANE", proc.stderr)
        self.assertIn("src/other.py", proc.stderr)

    def test_lane_owned_audit_surfaces_pass(self):
        self.repo.commit("docs/agent-logs/2026/06/12/run.md", "log\n")
        self.repo.commit("docs/status-notes/2026-06-12-T-100.md", "note\n")
        self.repo.commit("docs/explorations/2026-06-12-idea.md", "notes\n")
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_archive_destination_passes(self):
        self.repo.commit(f"docs/changes/archive/{TASK}/state.json", "{}\n")
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_views_with_fresh_base_pass(self):
        self.repo.commit("docs/roadmap.md", "# Roadmap v2\n")
        self.repo.commit("docs/project-status.md", "# Status v2\n")
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_views_with_stale_base_block_with_rebase_hint(self):
        self.repo.commit("docs/roadmap.md", "# Roadmap v2\n")
        self.repo.advance_main()
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, VIOLATION)
        self.assertIn("STALE VIEW", proc.stderr)
        self.assertIn("docs/roadmap.md", proc.stderr)
        self.assertIn("Rebase", proc.stderr)

    def test_allow_views_overrides_stale_base(self):
        self.repo.commit("docs/roadmap.md", "# Roadmap v2\n")
        self.repo.advance_main()
        proc = self.repo.fence("--task-id", TASK, "--allow-views")
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_stale_base_does_not_excuse_out_of_lane(self):
        self.repo.commit("src/other.py")
        self.repo.advance_main()
        proc = self.repo.fence("--task-id", TASK, "--allow-views")
        self.assertEqual(proc.returncode, VIOLATION)
        self.assertIn("OUT OF LANE", proc.stderr)

    def test_extra_allow_paths(self):
        self.repo.commit("src/other.py")
        proc = self.repo.fence("--task-id", TASK, "--allow", "src/other.py")
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_claim_touches_preferred_over_frontmatter(self):
        # frontmatter only covers src/widget.py; the live claim covers other.py
        self.repo.write_claim(["src/widget.py", "src/other.py"])
        self.repo.commit("src/other.py")
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_task_id_resolved_from_state(self):
        self.repo.write_state()
        self.repo.commit("src/widget.py")
        proc = self.repo.fence()
        self.assertEqual(proc.returncode, OK, proc.stderr)
        self.assertIn(TASK, proc.stdout)

    def test_no_task_id_exits_3(self):
        self.repo.commit("src/widget.py")
        proc = self.repo.fence()
        self.assertEqual(proc.returncode, NO_TASK)

    def test_no_changes_is_clean_pass(self):
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, OK, proc.stderr)
        self.assertIn("no changes", proc.stdout)

    def test_unresolvable_base_is_inapplicable_not_fatal(self):
        self.repo.commit("src/other.py")
        proc = self.repo.fence("--task-id", TASK, "--base", "no-such-ref")
        self.assertEqual(proc.returncode, OK)
        self.assertIn("inapplicable", proc.stderr)


class FenceAllowedTests(unittest.TestCase):
    def setUp(self):
        self.repo = FenceRepo()

    def tearDown(self):
        self.repo.cleanup()

    def test_allowed_prints_resolved_allowlist(self):
        proc = self.repo.fence("--task-id", TASK, sub="allowed")
        self.assertEqual(proc.returncode, OK, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["task"], TASK)
        self.assertIn("src/widget.py", payload["allowed"])
        self.assertIn(f"docs/changes/{TASK}/", payload["allowed"])
        self.assertIn("docs/status-notes/", payload["allowed"])
        self.assertIn("docs/roadmap.md", payload["views"])


if __name__ == "__main__":
    unittest.main()
