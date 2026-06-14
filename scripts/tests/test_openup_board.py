#!/usr/bin/env python3
"""Unit tests for scripts/openup-board.py (T-017).

Run with either:
    python3 -m unittest scripts.tests.test_openup_board
    python3 scripts/tests/test_openup_board.py

Hermetic: each test builds an isolated fixture repo (docs/changes/*/plan.md)
and an injected --claims-dir, so it never depends on the live repo or real
leases. The board is exercised through its CLI exactly as /openup-next would.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "openup-board.py"

OK, USAGE, NONE_PICKABLE = 0, 2, 3


def write_plan(root, task_id, *, title="T", status="ready", priority="medium",
               depends_on=None, touches=None, track=None, operations=None,
               completed=None):
    """Create docs/changes/<task_id>/plan.md with the given frontmatter + Operations."""
    folder = root / "docs" / "changes" / task_id
    folder.mkdir(parents=True, exist_ok=True)
    fm = [f"id: {task_id}", f"title: {title}", f"status: {status}",
          f"priority: {priority}"]
    fm.append("depends-on: [%s]" % ", ".join(depends_on or []))
    if touches:
        fm.append("touches: [%s]" % ", ".join(touches))
    if track is not None:
        fm.append(f"track: {track}")
    if completed is not None:
        fm.append(f"completed: {completed}")
    body = ["---", *fm, "---", "", f"# {task_id} — {title}", "", "## Operations", ""]
    if operations is None:
        operations = ["- [ ] do the thing"]
    body.extend(operations)
    body.append("")
    (folder / "plan.md").write_text("\n".join(body), encoding="utf-8")


def write_claim(cdir, task_id, touches, session="S1"):
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / f"{task_id}.json").write_text(json.dumps({
        "task_id": task_id, "session_id": session, "touches": touches,
        "branch": f"feature/{task_id}", "worktree": f"/tmp/wt-{task_id}",
        "claimed_at": "2026-01-01T00:00:00Z",
    }), encoding="utf-8")


def run(root, cdir, *cli, expect=None):
    out = root / ".openup" / "board.json"
    cmd = [sys.executable, str(SCRIPT), *cli,
           "--root", str(root), "--claims-dir", str(cdir), "--out", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if expect is not None:
        assert proc.returncode == expect, (
            f"expected exit {expect}, got {proc.returncode}\n"
            f"cli={cli}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def lanes(proc):
    return json.loads(proc.stdout)["lanes"]


def by_task(proc):
    return {l["task"]: l for l in lanes(proc)}


class BoardTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.cdir = self.root / "claims"  # deliberately absent until needed

    def tearDown(self):
        self._tmp.cleanup()

    # --- field set + ready lane -----------------------------------------
    def test_ready_lane_field_set(self):
        write_plan(self.root, "T-100", track="standard")
        lane = by_task(run(self.root, self.cdir, "refresh", expect=OK))["T-100"]
        self.assertEqual(set(lane), {
            "task", "title", "track", "state", "lease", "hat",
            "next_action", "plan", "collides_with", "depends_ok",
            "awaiting_input"})
        self.assertEqual(lane["state"], "ready")
        self.assertEqual(lane["track"], "standard")
        self.assertEqual(lane["lease"], None)
        self.assertEqual(lane["collides_with"], None)
        self.assertTrue(lane["depends_ok"])
        self.assertEqual(lane["next_action"], "do the thing")
        self.assertEqual(lane["hat"], "developer")
        self.assertEqual(lane["plan"], "docs/changes/T-100/plan.md")

    # --- dependency states ----------------------------------------------
    def test_blocked_on_unmet_dependency(self):
        write_plan(self.root, "T-101", depends_on=["T-999"])  # T-999 absent
        lane = by_task(run(self.root, self.cdir, "refresh", expect=OK))["T-101"]
        self.assertEqual(lane["state"], "blocked")
        self.assertFalse(lane["depends_ok"])

    def test_ready_when_dependency_done(self):
        write_plan(self.root, "T-050", status="done", completed="2026-01-01")
        write_plan(self.root, "T-102", depends_on=["T-050"])
        board = by_task(run(self.root, self.cdir, "refresh", expect=OK))
        self.assertNotIn("T-050", board, "done lanes are excluded from the board")
        self.assertEqual(board["T-102"]["state"], "ready")
        self.assertTrue(board["T-102"]["depends_ok"])

    # --- lease / collision ----------------------------------------------
    def test_in_progress_when_leased(self):
        write_plan(self.root, "T-103", touches=["src/a/"])
        write_claim(self.cdir, "T-103", ["src/a/"])
        lane = by_task(run(self.root, self.cdir, "refresh", expect=OK))["T-103"]
        self.assertEqual(lane["state"], "in-progress")
        self.assertEqual(lane["lease"]["session_id"], "S1")

    def test_colliding_with_foreign_lease(self):
        write_plan(self.root, "T-104", touches=["src/shared/"])
        write_claim(self.cdir, "T-OTHER", ["src/shared/widget.py"])  # foreign lease
        lane = by_task(run(self.root, self.cdir, "refresh", expect=OK))["T-104"]
        self.assertEqual(lane["state"], "colliding")
        self.assertEqual(lane["collides_with"], "T-OTHER")

    # --- checkbox parsing ------------------------------------------------
    def test_hat_role_tag_and_first_unchecked(self):
        ops = ["- [x] (developer) already done step",
               "- [ ] (tester) run the suite",
               "- [ ] (developer) later step"]
        write_plan(self.root, "T-105", operations=ops)
        lane = by_task(run(self.root, self.cdir, "refresh", expect=OK))["T-105"]
        self.assertEqual(lane["next_action"], "run the suite")
        self.assertEqual(lane["hat"], "tester")

    def test_legacy_numbered_operations_yields_null(self):
        write_plan(self.root, "T-106",
                   operations=["1. first step", "2. second step"])
        lane = by_task(run(self.root, self.cdir, "refresh", expect=OK))["T-106"]
        self.assertIsNone(lane["next_action"])
        self.assertIsNone(lane["hat"])
        self.assertEqual(lane["state"], "ready")  # still queueable

    def test_all_boxes_ticked_yields_null_next_action(self):
        write_plan(self.root, "T-107",
                   operations=["- [x] one", "- [x] two"])
        lane = by_task(run(self.root, self.cdir, "refresh", expect=OK))["T-107"]
        self.assertIsNone(lane["next_action"])
        self.assertIsNone(lane["hat"])

    # --- deferred / blocked passthrough ---------------------------------
    def test_deferred_status_passthrough(self):
        write_plan(self.root, "T-108", status="deferred")
        lane = by_task(run(self.root, self.cdir, "refresh", expect=OK))["T-108"]
        self.assertEqual(lane["state"], "deferred")

    # --- top selection + ordering ---------------------------------------
    def test_top_picks_pickable_lane(self):
        write_plan(self.root, "T-110", priority="low")
        write_plan(self.root, "T-111", priority="high")  # higher priority wins
        write_plan(self.root, "T-112", depends_on=["T-999"])  # blocked
        proc = run(self.root, self.cdir, "top", expect=OK)
        self.assertEqual(json.loads(proc.stdout)["task"], "T-111")

    def test_top_exits_cleanly_when_none_pickable(self):
        write_plan(self.root, "T-113", touches=["src/x/"])
        write_claim(self.cdir, "T-113", ["src/x/"])  # leased → in-progress
        proc = run(self.root, self.cdir, "top", expect=NONE_PICKABLE)
        self.assertIn("no pickable lane", proc.stderr)

    def test_top_empty_board_clean_stop(self):
        proc = run(self.root, self.cdir, "top", expect=NONE_PICKABLE)
        self.assertIn("no active lanes", proc.stderr)

    # --- determinism + side effect --------------------------------------
    def test_deterministic_output(self):
        write_plan(self.root, "T-120")
        write_plan(self.root, "T-121", priority="high")
        a = run(self.root, self.cdir, "refresh", expect=OK).stdout
        b = run(self.root, self.cdir, "refresh", expect=OK).stdout
        self.assertEqual(a, b, "identical inputs → byte-identical board")

    def test_writes_board_file(self):
        write_plan(self.root, "T-122")
        run(self.root, self.cdir, "refresh", expect=OK)
        out = self.root / ".openup" / "board.json"
        self.assertTrue(out.exists())
        self.assertEqual(json.loads(out.read_text())["lanes"][0]["task"], "T-122")

    def test_default_subcommand_is_refresh(self):
        write_plan(self.root, "T-123")
        # no subcommand token → defaults to refresh
        proc = run(self.root, self.cdir, expect=OK)
        self.assertEqual(by_task(proc)["T-123"]["state"], "ready")


if __name__ == "__main__":
    unittest.main()
