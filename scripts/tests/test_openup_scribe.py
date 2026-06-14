#!/usr/bin/env python3
"""Unit tests for scripts/openup-scribe.py.

Run with either:
    python3 -m unittest scripts.tests.test_openup_scribe
    python3 scripts/tests/test_openup_scribe.py
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "openup-scribe.py"


def run(args, stdin=None, expect_code=None):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True, text=True, input=stdin,
    )
    if expect_code is not None:
        assert proc.returncode == expect_code, (
            f"expected exit {expect_code}, got {proc.returncode}\n"
            f"args={args}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc


class StatusNoteTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_writes_dated_file_with_body(self):
        run(["status-note", "--task-id", "T-001", "--date", "2026-06-14",
             "--dir", str(self.dir), "--body", "- **Iteration 9**: did the thing"],
            expect_code=0)
        f = self.dir / "2026-06-14-T-001.md"
        self.assertTrue(f.exists())
        self.assertIn("did the thing", f.read_text())

    def test_body_from_stdin(self):
        run(["status-note", "--task-id", "T-002", "--date", "2026-06-14",
             "--dir", str(self.dir)],
            stdin="- summary via stdin\n", expect_code=0)
        self.assertIn("summary via stdin",
                      (self.dir / "2026-06-14-T-002.md").read_text())

    def test_collision_produces_second_file(self):
        for _ in range(2):
            run(["status-note", "--task-id", "T-003", "--date", "2026-06-14",
                 "--dir", str(self.dir), "--body", "- x"], expect_code=0)
        files = {p.name for p in self.dir.glob("2026-06-14-T-003*.md")}
        self.assertEqual(len(files), 2, files)
        # The first write takes the un-suffixed base name; the collision gets a suffix.
        self.assertIn("2026-06-14-T-003.md", files)
        self.assertTrue(any(n != "2026-06-14-T-003.md" for n in files), files)


class LearningsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.file = Path(self._tmp.name) / "memory" / "iteration-learnings.md"

    def tearDown(self):
        self._tmp.cleanup()

    def test_creates_and_appends(self):
        run(["learnings", "--task-id", "T-001", "--title", "First",
             "--date", "2026-06-14", "--file", str(self.file),
             "--what-worked", "tdd", "--decisions", "use sonnet",
             "--gotchas", "none", "--conventions", "marker blocks"],
            expect_code=0)
        text = self.file.read_text()
        self.assertIn("# Iteration Learnings", text)
        self.assertIn("## [2026-06-14] T-001: First", text)
        self.assertIn("- **Decisions made**: use sonnet", text)

        # Second call appends, keeps a single header.
        run(["learnings", "--task-id", "T-002", "--title", "Second",
             "--date", "2026-06-14", "--file", str(self.file),
             "--what-worked", "x"], expect_code=0)
        text = self.file.read_text()
        self.assertEqual(text.count("# Iteration Learnings"), 1)
        self.assertIn("## [2026-06-14] T-002: Second", text)


if __name__ == "__main__":
    unittest.main()
