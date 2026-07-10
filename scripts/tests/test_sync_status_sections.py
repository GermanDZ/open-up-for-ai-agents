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


if __name__ == "__main__":
    unittest.main()
