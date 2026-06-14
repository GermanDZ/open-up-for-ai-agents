#!/usr/bin/env python3
"""Unit tests for scripts/openup-input.py and the board's suspended state (T-033).

Run with either:
    python3 -m unittest scripts.tests.test_openup_input
    python3 scripts/tests/test_openup_input.py

Hermetic: each test builds an isolated fixture repo (docs/changes/*/plan.md +
docs/input-requests/*.md) and an injected --claims-dir, so it never touches the
live repo.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

INPUT_SCRIPT = Path(__file__).resolve().parents[1] / "openup-input.py"
BOARD_SCRIPT = Path(__file__).resolve().parents[1] / "openup-board.py"

OK, USAGE = 0, 2


def write_request(root, name, *, status, related_task=None, title="Q"):
    rdir = root / "docs" / "input-requests"
    rdir.mkdir(parents=True, exist_ok=True)
    fm = [f'title: "{title}"', f"status: {status}"]
    if related_task is not None:
        fm.append(f"related_task: {related_task}")
    body = ["---", *fm, "---", "", f"# {title}", "", "## Questions", ""]
    (rdir / name).write_text("\n".join(body), encoding="utf-8")
    return f"docs/input-requests/{name}"


def write_plan(root, task_id, *, status="ready", awaiting_input=None,
               touches=None):
    folder = root / "docs" / "changes" / task_id
    folder.mkdir(parents=True, exist_ok=True)
    fm = [f"id: {task_id}", f"title: {task_id}", f"status: {status}",
          "priority: medium", "depends-on: []"]
    if touches:
        fm.append("touches: [%s]" % ", ".join(touches))
    if awaiting_input is not None:
        fm.append(f"awaiting-input: {awaiting_input}")
    body = ["---", *fm, "---", "", f"# {task_id}", "", "## Operations", "",
            "- [ ] do the thing", ""]
    (folder / "plan.md").write_text("\n".join(body), encoding="utf-8")


def run_input(root, *cli, expect=None):
    cmd = [sys.executable, str(INPUT_SCRIPT), *cli, "--root", str(root)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if expect is not None:
        assert proc.returncode == expect, (
            f"expected exit {expect}, got {proc.returncode}\n"
            f"cli={cli}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def run_board(root, cdir):
    out = root / ".openup" / "board.json"
    cmd = [sys.executable, str(BOARD_SCRIPT), "refresh",
           "--root", str(root), "--claims-dir", str(cdir), "--out", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == OK, proc.stderr
    return {l["task"]: l for l in json.loads(proc.stdout)["lanes"]}


class ResumableTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.cdir = self.root / "claims"

    def tearDown(self):
        self._tmp.cleanup()

    # --- Success measure from the spec ----------------------------------
    def test_answered_request_is_resumable(self):
        write_request(self.root, "2026-06-14-vision.md",
                      status="answered", related_task="T-002")
        proc = run_input(self.root, "resumable", expect=OK)
        self.assertIn("T-002", proc.stdout)
        self.assertIn("docs/input-requests/2026-06-14-vision.md", proc.stdout)

    def test_pending_request_is_not_resumable(self):
        write_request(self.root, "2026-06-14-vision.md",
                      status="pending", related_task="T-002")
        proc = run_input(self.root, "resumable", expect=OK)
        self.assertEqual(proc.stdout.strip(), "")

    def test_no_requests_dir_is_clean_exit(self):
        proc = run_input(self.root, "resumable", expect=OK)
        self.assertEqual(proc.stdout.strip(), "")

    def test_answered_without_related_task_is_skipped(self):
        write_request(self.root, "orphan.md", status="answered")
        proc = run_input(self.root, "resumable", expect=OK)
        self.assertEqual(proc.stdout.strip(), "")

    def test_resumable_default_subcommand(self):
        write_request(self.root, "q.md", status="answered", related_task="T-009")
        # No explicit subcommand → defaults to `resumable`.
        proc = run_input(self.root, expect=OK)
        self.assertIn("T-009", proc.stdout)

    def test_resumable_json(self):
        write_request(self.root, "a.md", status="answered", related_task="T-002")
        write_request(self.root, "b.md", status="answered", related_task="T-001")
        proc = run_input(self.root, "resumable", "--json", expect=OK)
        rows = json.loads(proc.stdout)
        self.assertEqual([r["task"] for r in rows], ["T-001", "T-002"])

    def test_list_shows_open_requests(self):
        write_request(self.root, "a.md", status="pending", related_task="T-002")
        write_request(self.root, "b.md", status="answered", related_task="T-001")
        proc = run_input(self.root, "list", "--json", expect=OK)
        rows = json.loads(proc.stdout)
        self.assertEqual({r["status"] for r in rows}, {"pending", "answered"})


class BoardSuspendedTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.cdir = self.root / "claims"

    def tearDown(self):
        self._tmp.cleanup()

    def test_pending_input_makes_lane_suspended(self):
        req = write_request(self.root, "q.md", status="pending",
                            related_task="T-002")
        write_plan(self.root, "T-002", awaiting_input=req)
        lane = run_board(self.root, self.cdir)["T-002"]
        self.assertEqual(lane["state"], "suspended")
        self.assertEqual(lane["awaiting_input"], req)

    def test_answered_input_lane_is_not_suspended(self):
        req = write_request(self.root, "q.md", status="answered",
                            related_task="T-002")
        write_plan(self.root, "T-002", awaiting_input=req)
        lane = run_board(self.root, self.cdir)["T-002"]
        self.assertNotEqual(lane["state"], "suspended")
        self.assertIsNone(lane["awaiting_input"])

    def test_stale_pointer_to_missing_request_not_suspended(self):
        write_plan(self.root, "T-002",
                   awaiting_input="docs/input-requests/gone.md")
        lane = run_board(self.root, self.cdir)["T-002"]
        self.assertEqual(lane["state"], "ready")
        self.assertIsNone(lane["awaiting_input"])

    def test_lane_without_awaiting_input_unchanged(self):
        write_plan(self.root, "T-100")
        lane = run_board(self.root, self.cdir)["T-100"]
        self.assertEqual(lane["state"], "ready")
        self.assertIsNone(lane["awaiting_input"])


if __name__ == "__main__":
    unittest.main()
