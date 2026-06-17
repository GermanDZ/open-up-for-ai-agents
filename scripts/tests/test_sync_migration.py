#!/usr/bin/env python3
"""Tests for scripts/lib/migrate-data.sh — the T-047 sync-time data migration
that untracks T-046's now-derived agent-runs.jsonl.

Hermetic: each test builds a throwaway git repo and invokes the bash function
via `source <lib>; migrate_untrack_agent_runs <root> <dry>`.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "lib" / "migrate-data.sh"
REL = "docs/agent-logs/agent-runs.jsonl"


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=str(repo),
                          capture_output=True, text=True)


def run_migration(repo, dry="false"):
    return subprocess.run(
        ["bash", "-c",
         f'source "{LIB}"; migrate_untrack_agent_runs "{repo}" "{dry}"'],
        capture_output=True, text=True)


def is_tracked(repo, rel):
    return git(repo, "ls-files", "--error-unmatch", rel).returncode == 0


class MigrateUntrackTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "t@t")
        git(self.repo, "config", "user.name", "t")
        (self.repo / "docs" / "agent-logs").mkdir(parents=True)
        (self.repo / REL).write_text('{"event":"seed"}\n')
        (self.repo / "f.txt").write_text("x")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "seed")

    def tearDown(self):
        self._tmp.cleanup()

    def test_tracked_file_is_untracked_and_ignored(self):
        self.assertTrue(is_tracked(self.repo, REL))
        run_migration(self.repo)
        # untracked but still on disk
        self.assertFalse(is_tracked(self.repo, REL))
        self.assertTrue((self.repo / REL).exists())
        # listed in .gitignore exactly once
        gi = (self.repo / ".gitignore").read_text().splitlines()
        self.assertEqual(gi.count(REL), 1)

    def test_already_untracked_is_clean_noop(self):
        # remove from tracking first; migration must do nothing and not error
        git(self.repo, "rm", "--cached", "-q", REL)
        git(self.repo, "commit", "-qm", "untrack")
        before_gi = (self.repo / ".gitignore").read_text() \
            if (self.repo / ".gitignore").exists() else ""
        proc = run_migration(self.repo)
        self.assertEqual(proc.returncode, 0)
        after_gi = (self.repo / ".gitignore").read_text() \
            if (self.repo / ".gitignore").exists() else ""
        self.assertEqual(before_gi, after_gi)  # untouched

    def test_dry_run_changes_nothing(self):
        proc = run_migration(self.repo, dry="true")
        self.assertIn("DRY RUN", proc.stdout)
        self.assertTrue(is_tracked(self.repo, REL))  # still tracked

    def test_gitignore_not_duplicated(self):
        (self.repo / ".gitignore").write_text(f"{REL}\n")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "-qm", "pre-ignore")
        run_migration(self.repo)
        gi = (self.repo / ".gitignore").read_text().splitlines()
        self.assertEqual(gi.count(REL), 1)  # not appended again
        self.assertFalse(is_tracked(self.repo, REL))


if __name__ == "__main__":
    unittest.main()
