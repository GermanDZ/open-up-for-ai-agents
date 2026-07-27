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


class ViewsOnlyTests(unittest.TestCase):
    """T-157: --views-only regenerates the state-free parts of the two shared
    views so a post-completion view conflict can be recovered at all.

    Plain `sync-status.py` exits EXIT_NO_STATE (3) without `.openup/state.json`,
    which `openup-session.py end` archives at completion — so the documented
    'rebase and re-run' recipe was impossible in exactly the situation it is
    written for. Every test here runs with NO state file present.
    """

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.root = self.dir / "repo"
        (self.root / "docs").mkdir(parents=True)
        self.notes = self.root / "docs" / "status-notes"
        self.roadmap = self.root / "docs" / "roadmap.md"
        self.ps = self.root / "docs" / "project-status.md"
        self.state_dir = self.root / ".openup"   # deliberately never created
        self.roadmap.write_text(
            "# Roadmap\n\n"
            "| ID | Title | Status | Priority |\n"
            "|---|---|---|---|\n"
            "| T-200 | A table task | in-progress | high |\n\n"
            "## T-042: a section task\n"
            "**Status**: in-progress\n"
            "**Priority**: high\n",
            encoding="utf-8",
        )
        self.ps.write_text(
            "# Project Status\n\n"
            "**Phase**: construction\n"
            "**Iteration**: 107\n"
            "**Iteration Goal**: an older goal\n"
            "**Status**: completed\n"
            "**Lane Status**: completed\n"
            "**Current Task**: T-139\n"
            "**Last Updated**: 2026-01-01\n"
            "**Updated By**: sync-status.py\n\n"
            "## Open Action Items\n\n"
            "- an item that must survive\n\n"
            "## Notes\n\n"
            "- only the T-001 note\n",
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _note(self, name, body):
        self.notes.mkdir(parents=True, exist_ok=True)
        (self.notes / name).write_text(body, encoding="utf-8")

    def _run(self, *extra):
        cmd = [
            sys.executable, str(SYNC_STATUS), "--views-only",
            "--state-dir", str(self.state_dir),
            "--roadmap", str(self.roadmap),
            "--project-status", str(self.ps),
            "--notes-dir", str(self.notes),
            *extra,
        ]
        return subprocess.run(cmd, capture_output=True, text=True)

    def _header(self, text=None):
        """Everything above the ## Notes heading — the region req 4 freezes."""
        text = self.ps.read_text() if text is None else text
        return text.split("## Notes")[0]

    def test_runs_without_state_file(self):
        """Req 1: the whole point — no .openup/state.json, exit 0 not 3."""
        self.assertFalse((self.state_dir / "state.json").exists())
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("No state file at", proc.stderr)

    def test_plain_sync_still_fails_without_state(self):
        """The bug this fixes must stay reproducible without the flag —
        otherwise a later refactor could make --views-only redundant without
        anyone noticing the guard was what mattered."""
        proc = subprocess.run(
            [sys.executable, str(SYNC_STATUS),
             "--state-dir", str(self.state_dir),
             "--roadmap", str(self.roadmap),
             "--project-status", str(self.ps),
             "--notes-dir", str(self.notes)],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 3)
        self.assertIn("No state file at", proc.stderr)

    def test_reassembles_notes_newest_first(self):
        """Req 2: all shards land, newest-first, replacing the stale body."""
        self._note("2026-01-01-T-001.md", "- only the T-001 note\n")
        self._note("2026-01-02-T-002.md", "- the **T-002** note\n")
        self._note("2026-01-03-T-003.md", "- the **T-003** note\n")
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        ps = self.ps.read_text()
        for marker in ("T-001", "**T-002**", "**T-003**"):
            self.assertIn(marker, ps)
        self.assertLess(ps.index("T-003"), ps.index("T-002"))
        self.assertLess(ps.index("T-002"), ps.index("T-001"))

    def test_reconciles_archived_section(self):
        """Req 3: the state-free roadmap pass runs too, so one command
        restores both views."""
        (self.root / "docs" / "changes" / "archive" / "T-042").mkdir(parents=True)
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertRegex(
            self.roadmap.read_text(),
            r"## T-042: a section task\n\*\*Status\*\*: completed \(\d{4}-\d{2}-\d{2}\)",
        )

    def test_header_is_byte_identical(self):
        """Req 4: the no-go zone. Every line above ## Notes survives exactly —
        including the fields a normal sync run WOULD rewrite (Last Updated,
        Updated By), and the intervening ## Open Action Items section."""
        before = self._header()
        self._note("2026-01-03-T-003.md", "- a new note that rewrites the body\n")
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._header(), before)
        ps = self.ps.read_text()
        self.assertIn("**Iteration**: 107", ps)
        self.assertIn("**Current Task**: T-139", ps)
        self.assertIn("**Last Updated**: 2026-01-01", ps)
        self.assertIn("- an item that must survive", ps)
        # and the note really did land, so the assertion above is not vacuous
        self.assertIn("a new note that rewrites the body", ps)

    def test_table_row_status_untouched(self):
        """Req 4 corollary + the first Assumption: table-row cells have no
        state-free truth source, so they are deliberately out of scope."""
        (self.root / "docs" / "changes" / "archive" / "T-200").mkdir(parents=True)
        self._run()
        self.assertIn("| T-200 | A table task | in-progress | high |",
                      self.roadmap.read_text())

    def test_does_not_write_gate_or_state(self):
        """Req 5: no lane to gate. Even when a state file IS present, the
        state-free path must not touch it."""
        import json
        self.state_dir.mkdir(parents=True, exist_ok=True)
        sf = self.state_dir / "state.json"
        original = json.dumps({"task_id": "T-200", "track": "standard",
                               "gates": {"log_written": True}})
        sf.write_text(original, encoding="utf-8")
        self._note("2026-01-03-T-003.md", "- a note\n")
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(sf.read_text(), original)
        self.assertNotIn("roadmap_synced", sf.read_text())

    def test_dry_run_writes_nothing(self):
        """Req 6: reports the pending change, leaves both files byte-identical."""
        (self.root / "docs" / "changes" / "archive" / "T-042").mkdir(parents=True)
        self._note("2026-01-03-T-003.md", "- a note that would land\n")
        ps_before = self.ps.read_text()
        rm_before = self.roadmap.read_text()
        proc = self._run("--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("DRIFT T-042", proc.stdout)
        self.assertIn("stale", proc.stdout)
        self.assertEqual(self.ps.read_text(), ps_before)
        self.assertEqual(self.roadmap.read_text(), rm_before)

    def test_absent_notes_dir_is_a_clean_noop(self):
        """Second Assumption: a repo with no shards is legitimate, not an
        error. The roadmap pass must still run."""
        (self.root / "docs" / "changes" / "archive" / "T-042").mkdir(parents=True)
        ps_before = self.ps.read_text()
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.ps.read_text(), ps_before)
        self.assertIn("completed (", self.roadmap.read_text())

    def test_idempotent(self):
        self._note("2026-01-03-T-003.md", "- a note\n")
        self._run()
        ps1, rm1 = self.ps.read_text(), self.roadmap.read_text()
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.ps.read_text(), ps1)
        self.assertEqual(self.roadmap.read_text(), rm1)

    def test_missing_doc_reports_exit_4(self):
        self.ps.unlink()
        proc = self._run()
        self.assertEqual(proc.returncode, 4)
        self.assertIn("Missing doc", proc.stderr)


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
