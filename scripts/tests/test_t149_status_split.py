#!/usr/bin/env python3
"""T-149 — `**Status**` vs `**Lane Status**` in docs/project-status.md.

`sync-status.py` derives one value (the active lane's status) but the shared
view has to answer two questions, so it lands in two fields:

  **Status**       status of the iteration named in **Iteration** — written only
                   when the lane carries a real iteration number, so the pair
                   always agrees.
  **Lane Status**  status of the active lane — written on every sync.

Covers requirements 1-4 of docs/changes/T-149/plan.md (the writer side). The
hook side (requirements 5-6) lives in test_on_task_request_hook.py.

Run with either:
    python3 -m unittest scripts.tests.test_t149_status_split
    python3 scripts/tests/test_t149_status_split.py

Hermetic: isolated state dir, roadmap and project-status; the live repo's docs/
are never read or written.
"""

import json
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


# A completed iteration at rest: this is what a live lane must not rewrite.
HEADER = (
    "# Project Status\n\n"
    "**Phase**: construction\n"
    "**Iteration**: 104\n"
    "**Iteration Goal**: T-147 — a finished iteration\n"
    "**Status**: completed\n"
    "**Current Task**: T-147\n"
    "**Last Updated**: 2026-01-01\n"
    "**Updated By**: hand\n"
)


class StatusSplitTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.state_dir = self.dir / ".openup"
        self.roadmap = self.dir / "roadmap.md"
        self.ps = self.dir / "project-status.md"
        self.roadmap.write_text(
            "# Roadmap\n\n"
            "| ID | Title | Status | Priority | Depends on |\n"
            "|---|---|---|---|---|\n"
            "| T-999 | Split fixture | planned | high | — |\n"
        )
        self.ps.write_text(HEADER)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _init_state(self, *extra):
        state_cli(
            self.state_dir, "init", "--task-id", "T-999",
            "--phase", "construction",
            "--branch", "lane/T-999", "--worktree", str(self.dir), "--force",
            *extra,
        )

    def _run_sync(self):
        cmd = [
            sys.executable, str(SYNC_STATUS),
            "--state-dir", str(self.state_dir),
            "--roadmap", str(self.roadmap),
            "--project-status", str(self.ps),
            # Isolate from the live repo's docs/status-notes/ (T-024).
            "--notes-dir", str(self.dir / "no-status-notes"),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc

    # -- Requirement 1 -----------------------------------------------------
    def test_quick_lane_cannot_rewrite_a_completed_iterations_status(self):
        """The whole point of the task: a live quick lane must leave the
        recorded status of the last completed iteration alone."""
        self._init_state("--iteration", "0", "--track", "quick")
        self._run_sync()
        ps = self.ps.read_text()
        self.assertIn("**Status**: completed", ps)
        self.assertIn("**Iteration**: 104", ps)
        # The clobber signature the success measure watches for:
        self.assertNotIn("**Status**: in-progress", ps)

    def test_absent_iteration_key_also_preserves_status(self):
        """Falsiness, not `== 0` — `**Status**` inherits `**Iteration**`'s
        guard exactly (T-146 DD1), so a state file with no `iteration` key at
        all behaves like the quick-track sentinel."""
        self._init_state("--iteration", "0", "--track", "quick")
        sf = self.state_dir / "state.json"
        data = json.loads(sf.read_text())
        del data["iteration"]
        sf.write_text(json.dumps(data))
        self._run_sync()
        ps = self.ps.read_text()
        self.assertIn("**Status**: completed", ps)
        self.assertIn("**Iteration**: 104", ps)

    # -- Requirement 2 -----------------------------------------------------
    def test_real_iteration_still_writes_status(self):
        """The guard is narrow: a lane carrying a real iteration number writes
        both halves of the pair, so `Status` still describes `Iteration`."""
        self._init_state("--iteration", "105", "--track", "standard")
        self._run_sync()
        ps = self.ps.read_text()
        self.assertIn("**Iteration**: 105", ps)
        self.assertIn("**Status**: in-progress", ps)

    def test_iteration_and_status_always_move_together(self):
        """The invariant the split buys: across both branches of the guard,
        `**Status**` changes if and only if `**Iteration**` does."""
        for iteration, track in (("0", "quick"), ("105", "standard")):
            with self.subTest(iteration=iteration):
                self.ps.write_text(HEADER)
                self._init_state("--iteration", iteration, "--track", track)
                self._run_sync()
                ps = self.ps.read_text()
                iteration_moved = "**Iteration**: 104" not in ps
                status_moved = "**Status**: completed" not in ps
                self.assertEqual(iteration_moved, status_moved)

    # -- Requirement 3 -----------------------------------------------------
    def test_lane_status_written_on_a_falsy_iteration_lane(self):
        """`Lane Status` carries the value `Status` no longer can — this is
        what keeps on-task-request.py able to see a live quick lane."""
        self._init_state("--iteration", "0", "--track", "quick")
        self._run_sync()
        ps = self.ps.read_text()
        self.assertIn("**Lane Status**: in-progress", ps)
        self.assertIn("**Status**: completed", ps)

    def test_lane_status_written_on_a_real_iteration_lane_too(self):
        self._init_state("--iteration", "105", "--track", "standard")
        self._run_sync()
        self.assertIn("**Lane Status**: in-progress", self.ps.read_text())

    def test_lane_status_tracks_completion(self):
        self._init_state("--iteration", "105", "--track", "standard")
        for gate in ("log_written", "roadmap_synced",
                     "implementation_verified"):
            state_cli(self.state_dir, "set-gate", gate, "true")
        self._run_sync()
        self.assertIn("**Lane Status**: completed", self.ps.read_text())

    # -- Requirement 4 -----------------------------------------------------
    def test_lane_status_is_inserted_directly_after_status(self):
        """Upserted into documents that predate the field — a downstream repo
        must not have to hand-edit its header to upgrade."""
        self.assertNotIn("Lane Status", self.ps.read_text())
        self._init_state("--iteration", "105", "--track", "standard")
        self._run_sync()
        lines = self.ps.read_text().splitlines()
        i = next(n for n, ln in enumerate(lines)
                 if ln.startswith("**Status**:"))
        self.assertTrue(lines[i + 1].startswith("**Lane Status**:"))

    def test_upsert_does_not_add_other_missing_fields(self):
        """`set_field` stays replace-only. Making it insert-when-missing would
        materialize every absent header field in every un-migrated document."""
        self.ps.write_text(
            "# Project Status\n\n"
            "**Phase**: construction\n"
            "**Iteration**: 104\n"
            "**Status**: completed\n"
            "**Current Task**: T-147\n"
        )
        self._init_state("--iteration", "105", "--track", "standard")
        self._run_sync()
        ps = self.ps.read_text()
        self.assertIn("**Lane Status**:", ps)
        self.assertNotIn("**Iteration Goal**:", ps)
        self.assertNotIn("**Last Updated**:", ps)

    def test_second_sync_replaces_rather_than_duplicates(self):
        self._init_state("--iteration", "105", "--track", "standard")
        self._run_sync()
        first = self.ps.read_text()
        self._run_sync()
        second = self.ps.read_text()
        self.assertEqual(second.count("**Lane Status**:"), 1)
        self.assertEqual(first, second)

    def test_missing_anchor_is_a_no_op(self):
        """A hand-rolled document with no `**Status**` line is left alone
        rather than restructured — readers fall back instead."""
        self.ps.write_text(
            "# Project Status\n\n"
            "**Phase**: construction\n"
            "**Current Task**: T-147\n"
        )
        self._init_state("--iteration", "105", "--track", "standard")
        self._run_sync()
        ps = self.ps.read_text()
        self.assertNotIn("**Lane Status**:", ps)
        self.assertIn("**Current Task**: T-999", ps)   # the sync still ran


if __name__ == "__main__":
    unittest.main()
