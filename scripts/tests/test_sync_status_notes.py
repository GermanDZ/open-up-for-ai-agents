#!/usr/bin/env python3
"""Unit tests for the sharded status-notes assembly in sync-status.py (T-024).

Run with either:
    python3 -m unittest scripts.tests.test_sync_status_notes
    python3 scripts/tests/test_sync_status_notes.py

Hermetic: isolated state dir, roadmap, project-status, and --notes-dir; the
live repo's docs/status-notes/ is never read.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
STATE_CLI = SCRIPTS_DIR / "openup-state.py"
SYNC_STATUS = SCRIPTS_DIR / "sync-status.py"


def state_cli(state_dir, *args):
    cmd = [sys.executable, str(STATE_CLI), *args, "--state-dir", str(state_dir)]
    return subprocess.run(cmd, capture_output=True, text=True)


class SyncStatusNotesTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.state_dir = self.dir / ".openup"
        self.notes = self.dir / "status-notes"
        self.roadmap = self.dir / "roadmap.md"
        self.ps = self.dir / "project-status.md"
        self.roadmap.write_text(
            "# Roadmap\n\n"
            "| ID | Title | Status | Priority | Depends on |\n"
            "|---|---|---|---|---|\n"
            "| T-200 | Notes fixture | planned | high | — |\n"
        )
        self.ps.write_text(
            "# Project Status\n\n"
            "**Phase**: construction\n"
            "**Iteration**: 1\n"
            "**Iteration Goal**: old goal\n"
            "**Status**: planned\n"
            "**Current Task**: T-000\n"
            "**Last Updated**: 2026-01-01\n"
            "**Updated By**: hand\n\n"
            "## Notes\n\n"
            "- hand-written entry that assembly replaces\n"
        )
        state_cli(
            self.state_dir, "init", "--task-id", "T-200", "--iteration", "2",
            "--phase", "construction", "--track", "standard",
            "--branch", "lane/T-200", "--worktree", str(self.dir), "--force",
        )

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _run_sync(self):
        cmd = [
            sys.executable, str(SYNC_STATUS),
            "--state-dir", str(self.state_dir),
            "--roadmap", str(self.roadmap),
            "--project-status", str(self.ps),
            "--notes-dir", str(self.notes),
        ]
        return subprocess.run(cmd, capture_output=True, text=True)

    def _note(self, name, body):
        self.notes.mkdir(parents=True, exist_ok=True)
        (self.notes / name).write_text(body, encoding="utf-8")

    def test_absent_dir_leaves_notes_untouched(self):
        proc = self._run_sync()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("hand-written entry", self.ps.read_text())

    def test_assembles_newest_first_by_filename(self):
        self._note("2026-06-10-T-198.md", "- **older** entry\n")
        self._note("2026-06-12-T-200.md", "- **newer** entry\n")
        proc = self._run_sync()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        ps = self.ps.read_text()
        self.assertNotIn("hand-written entry", ps)
        self.assertLess(ps.index("**newer**"), ps.index("**older**"))
        # entries separated by a blank line under the heading
        self.assertIn("## Notes\n\n- **newer** entry\n\n- **older** entry\n", ps)

    def test_appends_section_when_heading_missing(self):
        self.ps.write_text(
            "# Project Status\n\n**Status**: planned\n**Current Task**: T-000\n"
        )
        self._note("2026-06-12-T-200.md", "- entry\n")
        proc = self._run_sync()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("## Notes\n\n- entry\n", self.ps.read_text())

    def test_preserves_following_sections(self):
        self.ps.write_text(
            self.ps.read_text() + "\n## Risks\n\n- a risk that must survive\n"
        )
        self._note("2026-06-12-T-200.md", "- entry\n")
        self._run_sync()
        ps = self.ps.read_text()
        self.assertIn("## Risks", ps)
        self.assertIn("a risk that must survive", ps)
        self.assertLess(ps.index("- entry"), ps.index("## Risks"))

    def test_idempotent(self):
        self._note("2026-06-12-T-200.md", "- entry\n")
        self._run_sync()
        ps1 = self.ps.read_text()
        rm1 = self.roadmap.read_text()
        self._run_sync()
        self.assertEqual(self.ps.read_text(), ps1)
        self.assertEqual(self.roadmap.read_text(), rm1)

    def test_linked_id_cell_matches(self):
        self.roadmap.write_text(
            "# Roadmap\n\n"
            "| ID | Title | Status | Priority |\n"
            "|---|---|---|---|\n"
            "| [T-200](changes/archive/T-200/plan.md) | Notes fixture | planned | high |\n"
        )
        proc = self._run_sync()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rm = self.roadmap.read_text()
        self.assertIn("| in-progress |", rm)
        self.assertIn("**Iteration Goal**: T-200 — Notes fixture", self.ps.read_text())

    def test_completed_cell_is_date_stamped_and_stable(self):
        for gate in ("team_deployed", "log_written", "roadmap_synced"):
            state_cli(self.state_dir, "set-gate", gate, "true")
        self._run_sync()
        rm = self.roadmap.read_text()
        self.assertRegex(rm, r"\|\s*completed \(\d{4}-\d{2}-\d{2}\)\s*\|")
        # idempotent: a second run keeps the original stamp
        self._run_sync()
        self.assertEqual(self.roadmap.read_text(), rm)


class DeriveStatusTests(unittest.TestCase):
    """T-041 F11: a solo standard task (team_deployed=false) must derive
    'completed' once log_written + roadmap_synced are set. Only 'full' gates on
    team_deployed."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location("sync_status", SYNC_STATUS)
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def _state(self, track, **gates):
        base = {"team_deployed": False, "log_written": False,
                "roadmap_synced": False}
        base.update(gates)
        return {"track": track, "gates": base}

    def test_standard_solo_completes(self):
        s = self._state("standard", log_written=True, roadmap_synced=True)
        self.assertEqual(self.mod.derive_status(s), "completed")

    def test_standard_in_progress_until_gates(self):
        s = self._state("standard", log_written=True)  # roadmap_synced False
        self.assertEqual(self.mod.derive_status(s), "in-progress")

    def test_full_still_requires_team(self):
        s = self._state("full", log_written=True, roadmap_synced=True)
        self.assertEqual(self.mod.derive_status(s), "in-progress")
        s2 = self._state("full", team_deployed=True, log_written=True,
                         roadmap_synced=True)
        self.assertEqual(self.mod.derive_status(s2), "completed")


if __name__ == "__main__":
    unittest.main()
