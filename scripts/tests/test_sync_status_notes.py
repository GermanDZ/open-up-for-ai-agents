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

    def test_single_run_completes_when_gates_met(self):
        # G3: with log_written set and roadmap_synced still false, ONE sync run
        # must stamp `completed` — the run sets roadmap_synced itself, so the
        # status derivation reflects that (no "two-run dance").
        state_cli(self.state_dir, "set-gate", "log_written", "true")
        state_cli(self.state_dir, "set-gate", "implementation_verified", "true")
        proc = self._run_sync()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("status=completed", proc.stdout)
        self.assertRegex(self.roadmap.read_text(),
                         r"T-200 .*completed \(\d{4}-\d{2}-\d{2}\)")

    def test_bookkeeping_only_state_does_not_complete(self):
        """T-145 regression: `log_written` + `roadmap_synced` are both
        bookkeeping — satisfiable by process steps that run whether or not any
        work happened. Without the delivery-evidence gate the run must derive
        `in-progress`, never `completed`."""
        state_cli(self.state_dir, "set-gate", "log_written", "true")
        state_cli(self.state_dir, "set-gate", "roadmap_synced", "true")
        proc = self._run_sync()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("status=in-progress", proc.stdout)
        self.assertIn("| in-progress |", self.roadmap.read_text())
        self.assertIn("**Status**: in-progress", self.ps.read_text())

    def test_quick_track_also_requires_delivery_evidence(self):
        """The quick track is relaxed on ceremony, never on evidence."""
        state_cli(
            self.state_dir, "init", "--task-id", "T-200", "--iteration", "0",
            "--phase", "construction", "--track", "quick",
            "--branch", "quick/T-200", "--worktree", str(self.dir), "--force",
        )
        state_cli(self.state_dir, "set-gate", "log_written", "true")
        proc = self._run_sync()
        self.assertIn("status=in-progress", proc.stdout)
        state_cli(self.state_dir, "set-gate", "implementation_verified", "true")
        proc = self._run_sync()
        self.assertIn("status=completed", proc.stdout)

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

    def _init_state(self, *extra):
        state_cli(
            self.state_dir, "init", "--task-id", "T-200",
            "--phase", "construction",
            "--branch", "lane/T-200", "--worktree", str(self.dir), "--force",
            *extra,
        )

    def test_falsy_iteration_leaves_shared_header_untouched(self):
        """T-146: /openup-quick-task initializes state with the literal
        `--iteration 0` sentinel. Writing that into the project-wide header
        rewrote a real counter to 0 (observed downstream)."""
        self._init_state("--iteration", "0", "--track", "quick")
        proc = self._run_sync()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("**Iteration**: 1", self.ps.read_text())
        self.assertNotIn("**Iteration**: 0", self.ps.read_text())

    def test_absent_iteration_key_leaves_header_untouched(self):
        """Falsiness, not `== 0`: a state file with no `iteration` key at all
        behaves identically to the quick-track sentinel."""
        import json
        self._init_state("--iteration", "0", "--track", "quick")
        sf = self.state_dir / "state.json"
        data = json.loads(sf.read_text())
        del data["iteration"]
        sf.write_text(json.dumps(data))
        proc = self._run_sync()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("**Iteration**: 1", self.ps.read_text())

    def test_real_iteration_number_still_written(self):
        """The guard is narrow — a lane that does carry an iteration number
        still writes it."""
        self._init_state("--iteration", "96", "--track", "standard")
        proc = self._run_sync()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("**Iteration**: 96", self.ps.read_text())

    def test_falsy_iteration_still_syncs_every_other_field(self):
        """Skipping `Iteration` must not degrade into 'quick lanes don't sync'.

        T-149 moved the lane's status out of `**Status**` and into
        `**Lane Status**`: `**Status**` now sits behind the same guard as
        `**Iteration**` (it describes that iteration, so the pair moves
        together), while `**Lane Status**` carries the value this assertion
        originally checked. The subject of the test is unchanged — a quick lane
        still syncs everything that is not iteration-scoped.
        """
        self._init_state("--iteration", "0", "--track", "quick")
        proc = self._run_sync()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        ps = self.ps.read_text()
        self.assertIn("**Current Task**: T-200", ps)
        self.assertIn("**Phase**: construction", ps)
        self.assertIn("**Lane Status**: in-progress", ps)
        self.assertIn("**Status**: planned", ps)   # the fixture's value, preserved
        self.assertIn("**Updated By**: sync-status.py", ps)
        self.assertNotIn("**Last Updated**: 2026-01-01", ps)
        self.assertIn("| in-progress |", self.roadmap.read_text())

    def test_completed_cell_is_date_stamped_and_stable(self):
        for gate in ("team_deployed", "log_written", "roadmap_synced",
                     "implementation_verified"):
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
    team_deployed.

    T-145: every track additionally requires `implementation_verified` — the
    only gate in the set that evidences delivery rather than bookkeeping."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location("sync_status", SYNC_STATUS)
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def _state(self, track, **gates):
        base = {"team_deployed": False, "log_written": False,
                "roadmap_synced": False, "implementation_verified": False}
        base.update(gates)
        return {"track": track, "gates": base}

    def test_standard_solo_completes(self):
        s = self._state("standard", log_written=True, roadmap_synced=True,
                        implementation_verified=True)
        self.assertEqual(self.mod.derive_status(s), "completed")

    def test_standard_in_progress_until_gates(self):
        s = self._state("standard", log_written=True)  # roadmap_synced False
        self.assertEqual(self.mod.derive_status(s), "in-progress")

    def test_full_still_requires_team(self):
        s = self._state("full", log_written=True, roadmap_synced=True,
                        implementation_verified=True)
        self.assertEqual(self.mod.derive_status(s), "in-progress")
        s2 = self._state("full", team_deployed=True, log_written=True,
                         roadmap_synced=True, implementation_verified=True)
        self.assertEqual(self.mod.derive_status(s2), "completed")

    def test_every_track_requires_delivery_evidence(self):
        """T-145: bookkeeping gates alone never derive `completed`, on any
        track — including `quick`, which relaxes ceremony, not evidence."""
        for track in ("quick", "standard", "full"):
            with self.subTest(track=track):
                s = self._state(track, team_deployed=True, log_written=True,
                                roadmap_synced=True)
                self.assertEqual(self.mod.derive_status(s), "in-progress")
                s["gates"]["implementation_verified"] = True
                self.assertEqual(self.mod.derive_status(s), "completed")

    def test_absent_verified_key_reads_falsy(self):
        """The schema keeps the key optional, so a state file written before the
        gate existed must derive `in-progress` (not verified), not crash."""
        legacy = {"track": "standard",
                  "gates": {"log_written": True, "roadmap_synced": True}}
        self.assertEqual(self.mod.derive_status(legacy), "in-progress")


if __name__ == "__main__":
    unittest.main()
