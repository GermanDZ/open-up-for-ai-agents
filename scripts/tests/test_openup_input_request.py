#!/usr/bin/env python3
"""Unit tests for `openup-input.py request` — the deterministic input-request
creator (T-074).

Run with either:
    python3 -m unittest scripts.tests.test_openup_input_request
    python3 scripts/tests/test_openup_input_request.py

Hermetic: each test builds an isolated tmp repo and drives the CLI via
subprocess, exactly as the reference driver's ask_user (async) path does.
Also proves the round-trip: a driver-created request, once answered, is picked
up by the UNCHANGED `resumable` path.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "openup-input.py"


def _run(root, *args):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--root", str(root)],
        capture_output=True, text=True)
    return proc


class RequestCreationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _plan(self, task):
        d = self.root / "docs" / "changes" / task
        d.mkdir(parents=True)
        (d / "plan.md").write_text("---\nid: %s\nstatus: ready\n---\n# %s\n" % (task, task))
        return d / "plan.md"

    def test_creates_wellformed_request(self):
        p = _run(self.root, "request", "--title", "Which DB?",
                 "--question", "pg or mysql?", "--option", "pg", "--option", "mysql",
                 "--date", "2026-07-12", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        out = json.loads(p.stdout)
        f = self.root / out["request"]
        self.assertTrue(f.exists())
        text = f.read_text()
        self.assertIn("status: pending", text)
        self.assertIn("**Type**: multiple-choice", text)
        self.assertIn("- [ ] `pg`", text)
        self.assertIn("**Answer**:", text)
        self.assertEqual(out["request"], "docs/input-requests/2026-07-12-which-db.md")

    def test_text_question_when_no_options(self):
        p = _run(self.root, "request", "--title", "Name?", "--question", "your name?",
                 "--date", "2026-07-12", "--json")
        text = (self.root / json.loads(p.stdout)["request"]).read_text()
        self.assertIn("**Type**: text", text)

    def test_suspends_lane_when_task_folder_exists(self):
        plan = self._plan("T-9")
        p = _run(self.root, "request", "--task-id", "T-9", "--title", "Q",
                 "--question", "q?", "--date", "2026-07-12", "--json")
        out = json.loads(p.stdout)
        self.assertTrue(out["suspended"])
        pt = plan.read_text()
        self.assertIn("awaiting-input: docs/input-requests/2026-07-12-q.md", pt)
        # related_task recorded so `resumable` can map it back to the lane
        self.assertIn('related_task: "T-9"', (self.root / out["request"]).read_text())

    def test_no_task_id_leaves_plans_untouched(self):
        p = _run(self.root, "request", "--title", "Q", "--question", "q?",
                 "--date", "2026-07-12", "--json")
        out = json.loads(p.stdout)
        self.assertFalse(out["suspended"])
        self.assertIsNone(out["task"])

    def test_missing_task_folder_creates_request_but_no_suspend(self):
        # --task-id given but no change folder → request still created, no suspend
        p = _run(self.root, "request", "--task-id", "T-404", "--title", "Q",
                 "--question", "q?", "--date", "2026-07-12", "--json")
        out = json.loads(p.stdout)
        self.assertFalse(out["suspended"])

    def test_second_request_replaces_awaiting_input_line(self):
        plan = self._plan("T-9")
        _run(self.root, "request", "--task-id", "T-9", "--title", "First",
             "--question", "a?", "--date", "2026-07-11", "--json")
        _run(self.root, "request", "--task-id", "T-9", "--title", "Second",
             "--question", "b?", "--date", "2026-07-12", "--json")
        # exactly one awaiting-input line, pointing at the latest request
        lines = [l for l in plan.read_text().splitlines() if l.startswith("awaiting-input:")]
        self.assertEqual(len(lines), 1)
        self.assertIn("2026-07-12-second.md", lines[0])

    def test_round_trip_answered_request_is_resumable(self):
        self._plan("T-9")
        out = json.loads(_run(self.root, "request", "--task-id", "T-9", "--title", "Q",
                              "--question", "q?", "--date", "2026-07-12", "--json").stdout)
        req = self.root / out["request"]
        req.write_text(req.read_text().replace("status: pending", "status: answered"))
        res = _run(self.root, "resumable", "--json")
        rows = json.loads(res.stdout)
        self.assertEqual(rows, [{"task": "T-9", "request": out["request"]}])


if __name__ == "__main__":
    unittest.main()
