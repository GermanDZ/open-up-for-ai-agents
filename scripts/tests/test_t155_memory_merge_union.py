#!/usr/bin/env python3
"""T-155 — merge=union for the two shared .claude/memory/ append-only files.

Covers requirements 3-6 of docs/changes/T-155/plan.md: the consumer-side patch
that reaches projects which ALREADY exist. Requirements 1-2 (the framework's own
.gitattributes, and what a fresh bootstrap ships) live in
test_consumer_smoke.py, against a really-bootstrapped project.

The delivery half is the point of this task: bootstrap-project.sh copies
.gitattributes only at FIRST install, so without this patch the attribute reaches
new projects only — and never the existing ones where the collision occurs.

Hermetic: each test builds a throwaway directory and invokes the bash function
directly (`source <lib>; migrate_gitattributes_merge_union <root> <dry>`), the
same idiom as test_sync_migration.py.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "lib" / "migrate-data.sh"
ENTRIES = (".claude/memory/bypass-log.md",
           ".claude/memory/iteration-learnings.md")


def run_patch(root, dry="false"):
    return subprocess.run(
        ["bash", "-c",
         f'source "{LIB}"; migrate_gitattributes_merge_union "{root}" "{dry}"'],
        capture_output=True, text=True)


class GitattributesMergeUnionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.ga = self.root / ".gitattributes"

    def tearDown(self):
        self._tmp.cleanup()

    def _lines(self):
        return self.ga.read_text().splitlines()

    # -- Requirement 3 -----------------------------------------------------
    def test_adds_entries_and_preserves_existing_content(self):
        """The consumer shape that matters: a .gitattributes that already exists
        and carries the project's own lines. Those must survive."""
        self.ga.write_text("* text=auto\n"
                           "*.rb linguist-language=Ruby\n")
        proc = run_patch(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        lines = self._lines()
        for entry in ENTRIES:
            self.assertIn(f"{entry} merge=union", lines)
        # pre-existing lines untouched
        self.assertIn("* text=auto", lines)
        self.assertIn("*.rb linguist-language=Ruby", lines)

    def test_reports_what_it_did(self):
        self.ga.write_text("* text=auto\n")
        proc = run_patch(self.root)
        self.assertIn("Patched .gitattributes", proc.stdout)

    # -- Requirement 4 -----------------------------------------------------
    def test_second_run_is_a_byte_identical_no_op(self):
        self.ga.write_text("* text=auto\n")
        run_patch(self.root)
        first = self.ga.read_text()
        proc = run_patch(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.ga.read_text(), first)
        self.assertEqual(proc.stdout.strip(), "")   # nothing to report

    def test_each_entry_appears_exactly_once_after_repeated_runs(self):
        self.ga.write_text("* text=auto\n")
        for _ in range(3):
            run_patch(self.root)
        body = self.ga.read_text()
        for entry in ENTRIES:
            self.assertEqual(body.count(entry), 1)

    def test_a_consumers_own_variant_is_left_alone(self):
        """Matching is on the PATH, not the whole line — a project that chose a
        different driver for one of these files keeps its choice instead of
        getting a second, contradicting entry."""
        self.ga.write_text("* text=auto\n"
                           ".claude/memory/bypass-log.md merge=ours\n")
        run_patch(self.root)
        body = self.ga.read_text()
        self.assertIn(".claude/memory/bypass-log.md merge=ours", body)
        self.assertNotIn(".claude/memory/bypass-log.md merge=union", body)
        # the other entry is still added
        self.assertIn(".claude/memory/iteration-learnings.md merge=union", body)

    # -- Requirement 5 -----------------------------------------------------
    def test_creates_the_file_when_the_project_has_none(self):
        """The cqecho-app shape, verified 2026-07-27: a consumer with no
        .gitattributes at all."""
        self.assertFalse(self.ga.exists())
        proc = run_patch(self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(self.ga.exists())
        for entry in ENTRIES:
            self.assertIn(f"{entry} merge=union", self._lines())

    def test_created_file_states_the_local_only_caveat(self):
        """The honesty invariant: this is a mitigation, and the file it writes
        into a consumer must not imply otherwise."""
        run_patch(self.root)
        body = self.ga.read_text()
        self.assertIn("LOCAL", body)
        self.assertIn("server-side", body)

    # -- Requirement 6 -----------------------------------------------------
    def test_dry_run_reports_without_writing(self):
        self.ga.write_text("* text=auto\n")
        proc = run_patch(self.root, dry="true")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("[DRY RUN]", proc.stdout)
        for entry in ENTRIES:
            self.assertIn(entry, proc.stdout)
        self.assertEqual(self.ga.read_text(), "* text=auto\n")

    def test_dry_run_does_not_create_a_missing_file(self):
        proc = run_patch(self.root, dry="true")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(self.ga.exists())


if __name__ == "__main__":
    unittest.main()
