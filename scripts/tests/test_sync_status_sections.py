#!/usr/bin/env python3
"""Unit tests for section-style ``## T-NNN:`` roadmap Status stamping (T-067).

Covers the root-cause fix for plan-feature status-rot:
  * update_roadmap() falls back to the section ``**Status**:`` line when no
    table row matches (req 1) while leaving table rows untouched (req 2);
  * --reconcile self-heals archived sections idempotently (req 3);
  * openup-doctor surfaces the drift as a read-only WARNING (req 4).

Run with either:
    python3 -m unittest scripts.tests.test_sync_status_sections
    python3 scripts/tests/test_sync_status_sections.py

Hermetic: temp dirs only; the live repo's docs/roadmap.md is never touched.
"""

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SYNC_STATUS = SCRIPTS_DIR / "sync-status.py"
DOCTOR = SCRIPTS_DIR / "openup-doctor.py"
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ss = _load("sync_status", SYNC_STATUS)
doctor = _load("openup_doctor", DOCTOR)


ROADMAP = (
    "# Roadmap\n\n"
    "| ID | Title | Status | Priority | Depends on |\n"
    "|---|---|---|---|---|\n"
    "| T-062 | A table task | completed (2026-01-01) | high | — |\n\n"
    "## T-063: a section task\n"
    "**Status**: pending\n"
    "**Priority**: high\n\n"
    "## T-066: another section task\n"
    "**Status**: ready\n"
    "**Priority**: medium\n"
)


class UpdateRoadmapSectionTests(unittest.TestCase):
    def test_section_fallback_stamps_status_line(self):
        # req 1: no table row for T-066 → its section Status line is stamped.
        new, title = ss.update_roadmap(ROADMAP, "T-066", "completed", TODAY)
        self.assertIn(f"**Status**: completed ({TODAY})", new)
        self.assertEqual(title, "another section task")
        # the OTHER section and the table row are untouched
        self.assertIn("## T-063: a section task\n**Status**: pending", new)
        self.assertIn("| T-062 | A table task | completed (2026-01-01) |", new)

    def test_table_row_path_unchanged_no_section_touched(self):
        # req 2: a table id still flips the cell; no section edit is attempted.
        new, title = ss.update_roadmap(ROADMAP, "T-062", "completed", TODAY)
        self.assertEqual(title, "A table task")
        self.assertIn("| T-062 | A table task | completed (2026-01-01) |", new)
        # sections remain exactly as they were
        self.assertIn("## T-066: another section task\n**Status**: ready", new)

    def test_section_completed_is_idempotent(self):
        once, _ = ss.update_roadmap(ROADMAP, "T-063", "completed", TODAY)
        twice, _ = ss.update_roadmap(once, "T-063", "completed", "2099-12-31")
        # the second run keeps the first date (idempotent stamp)
        self.assertEqual(once, twice)
        self.assertIn(f"**Status**: completed ({TODAY})", twice)

    def test_missing_section_is_a_noop(self):
        new, title = ss.update_roadmap(ROADMAP, "T-999", "completed", TODAY)
        self.assertEqual(new, ROADMAP)
        self.assertIsNone(title)


class ReconcileTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "docs").mkdir()
        (self.root / "docs" / "roadmap.md").write_text(ROADMAP, encoding="utf-8")
        arch = self.root / "docs" / "changes" / "archive"
        # T-063 & T-066 are archived (should reconcile); T-066 only, plus one
        # archived id with NO section (must be skipped silently).
        for tid in ("T-063", "T-066", "T-500"):
            (arch / tid).mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_drift_lists_only_archived_noncompleted_sections(self):
        text = (self.root / "docs" / "roadmap.md").read_text()
        drift = dict(ss.section_status_drift(text, self.root))
        self.assertEqual(set(drift), {"T-063", "T-066"})
        self.assertEqual(drift["T-063"], "pending")
        self.assertEqual(drift["T-066"], "ready")

    def test_reconcile_stamps_and_is_idempotent(self):
        # archival_date falls back to today outside a git repo — assert that.
        text = (self.root / "docs" / "roadmap.md").read_text()
        new, changed = ss.reconcile_sections(text, self.root, TODAY)
        self.assertEqual({c[0] for c in changed}, {"T-063", "T-066"})
        self.assertIn(f"## T-063: a section task\n**Status**: completed ({TODAY})", new)
        self.assertIn(f"## T-066: another section task\n**Status**: completed ({TODAY})", new)
        # second pass: nothing changes
        again, changed2 = ss.reconcile_sections(new, self.root, "2099-01-01")
        self.assertEqual(changed2, [])
        self.assertEqual(again, new)

    def test_reconcile_cli_writes_and_reports(self):
        rm = self.root / "docs" / "roadmap.md"
        proc = subprocess.run(
            [sys.executable, str(SYNC_STATUS), "--reconcile", "--roadmap", str(rm)],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("reconciled 2 section(s)", proc.stdout)
        self.assertRegex(rm.read_text(), r"## T-063:.*\n\*\*Status\*\*: completed \(\d{4}-\d{2}-\d{2}\)")
        # dry-run reports drift without writing
        before = rm.read_text()
        dry = subprocess.run(
            [sys.executable, str(SYNC_STATUS), "--reconcile", "--dry-run",
             "--roadmap", str(rm)],
            capture_output=True, text=True,
        )
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertIn("drift: 0 section(s)", dry.stdout)
        self.assertEqual(rm.read_text(), before)


class DoctorDriftCheckTests(unittest.TestCase):
    """req 4: openup-doctor surfaces drift as a read-only WARNING and never
    writes. Uses a fixture repo with a COPIED sync-status.py so its REPO_ROOT
    resolves to the fixture (a symlink would resolve back to the live repo)."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "scripts").mkdir()
        shutil.copy(SYNC_STATUS, self.root / "scripts" / "sync-status.py")
        (self.root / "docs").mkdir()
        (self.root / "docs" / "roadmap.md").write_text(ROADMAP, encoding="utf-8")
        (self.root / "docs" / "changes" / "archive" / "T-063").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_warning_finding_and_no_write(self):
        before = (self.root / "docs" / "roadmap.md").read_text()
        findings = doctor.check_section_status_drift(str(self.root))
        drift = [f for f in findings if f.check == "roadmap-status-drift"]
        self.assertTrue(drift, "expected a drift finding")
        self.assertEqual(drift[0].severity, doctor.WARNING)
        self.assertIn("T-063", drift[0].message)
        self.assertIn("--reconcile", drift[0].message)
        # doctor must not have written anything
        self.assertEqual((self.root / "docs" / "roadmap.md").read_text(), before)

    def test_no_finding_when_completed(self):
        rm = self.root / "docs" / "roadmap.md"
        rm.write_text(ROADMAP.replace("**Status**: pending",
                                      "**Status**: completed (2026-01-01)"))
        findings = doctor.check_section_status_drift(str(self.root))
        drift = [f for f in findings
                 if f.check == "roadmap-status-drift" and f.severity == doctor.WARNING]
        self.assertEqual(drift, [])


class UnmatchedTaskReportingTests(unittest.TestCase):
    """T-159 / iteration-109 C3: sync-status must not claim success for a task it
    cannot find.

    Observed live in T-158: with no roadmap entry for the task, the run printed
    `Synced roadmap + project-status for T-158 (status=completed).` and wrote
    nothing to the roadmap. `update_roadmap()` returns the text unchanged when
    neither a table row nor a `## T-NNN:` section matches, but `main()` printed
    its success line unconditionally.
    """

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.root = self.dir / "repo"
        (self.root / "docs").mkdir(parents=True)
        self.state_dir = self.root / ".openup"
        self.roadmap = self.root / "docs" / "roadmap.md"
        self.ps = self.root / "docs" / "project-status.md"
        self.roadmap.write_text(ROADMAP, encoding="utf-8")
        self.ps.write_text(
            "# Project Status\n\n**Phase**: construction\n**Iteration**: 7\n"
            "**Status**: planned\n**Current Task**: T-000\n"
            "**Last Updated**: 2026-01-01\n**Updated By**: hand\n\n"
            "## Notes\n\n- a note\n",
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _init_state(self, task_id):
        subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "openup-state.py"), "init",
             "--task-id", task_id, "--iteration", "7", "--phase", "construction",
             "--track", "standard", "--branch", "b", "--worktree", str(self.root),
             "--state-dir", str(self.state_dir), "--force"],
            capture_output=True, text=True,
        )

    def _sync(self):
        return subprocess.run(
            [sys.executable, str(SYNC_STATUS),
             "--state-dir", str(self.state_dir),
             "--roadmap", str(self.roadmap),
             "--project-status", str(self.ps),
             "--notes-dir", str(self.root / "docs" / "status-notes")],
            capture_output=True, text=True,
        )

    # --- req 5: update_roadmap reports whether it matched -----------------
    def test_has_entry_true_for_idempotent_section(self):
        """`changed` cannot serve as the signal: a section already carrying the
        right status is unchanged but definitely FOUND."""
        text = ROADMAP.replace("**Status**: pending",
                               "**Status**: completed (2026-01-01)")
        self.assertTrue(ss.roadmap_has_entry(text, "T-063"),
                        "an idempotent section match must still count as found")

    def test_has_entry_false_for_absent_id(self):
        self.assertFalse(ss.roadmap_has_entry(ROADMAP, "T-900"))

    def test_has_entry_true_for_table_row(self):
        self.assertTrue(ss.roadmap_has_entry(ROADMAP, "T-062"))

    def test_has_entry_matches_linked_id_cell(self):
        """Row ids may be markdown links — reuse of `_id_cell_matches` means this
        works without a second implementation."""
        text = ROADMAP.replace("| T-062 |", "| [T-062](changes/archive/T-062/plan.md) |")
        self.assertTrue(ss.roadmap_has_entry(text, "T-062"))

    def test_update_roadmap_signature_unchanged(self):
        """Requirement 8 guard: five pre-existing tests unpack this as a 2-tuple.
        Widening it is what the mid-lane design correction avoided."""
        result = ss.update_roadmap(ROADMAP, "T-062", "completed", TODAY)
        self.assertEqual(len(result), 2)

    # --- req 6: main() warns instead of claiming success ------------------
    def test_unmatched_task_warns_on_stderr_and_exits_zero(self):
        self._init_state("T-777")
        proc = self._sync()
        self.assertEqual(proc.returncode, 0,
                         "must stay 0 — three callers treat non-zero as fatal")
        self.assertIn("T-777", proc.stderr)
        self.assertNotIn("Synced roadmap + project-status for T-777", proc.stdout)

    # --- req 7: a matching run is unchanged -------------------------------
    def test_matched_task_output_unchanged(self):
        self._init_state("T-062")
        proc = self._sync()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Synced roadmap + project-status for T-062", proc.stdout)
        self.assertEqual(proc.stderr.strip(), "",
                         "a matching run must emit no warning")


if __name__ == "__main__":
    unittest.main()
