#!/usr/bin/env python3
"""Unit tests for scripts/render-skills-mirror.py (T-071 increment 2).

Run with either:
    python3 -m unittest scripts.tests.test_render_skills_mirror
    python3 scripts/tests/test_render_skills_mirror.py
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "render-skills-mirror.py"

TIER_MAP = """claude-code:
  scribe: haiku
  reasoning: inherit
"""

PROC = """---
name: openup-demo
description: demo procedure
tier: reasoning
capabilities:
  required: [read_write_files, exec]
---

# Demo

Body line.
"""

# What render(pack) should produce for the fixture above: tier -> model, drop caps.
EXPECTED = """---
name: openup-demo
description: demo procedure
model: inherit
---

# Demo

Body line.
"""


def run(args, expect_code=None):
    cmd = [sys.executable, str(SCRIPT)] + args
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if expect_code is not None:
        assert proc.returncode == expect_code, (
            f"expected exit {expect_code}, got {proc.returncode}\n"
            f"args={args}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc


class LiveRepoTests(unittest.TestCase):
    """The checked-in mirror must always equal render(pack)."""

    def test_live_repo_is_in_sync(self):
        proc = run(["--check"], expect_code=0)
        self.assertIn("in sync", proc.stdout)


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.pack = self.root / "procedures"
        self.mirror = self.root / "skills"
        self.pack.mkdir()
        self.tier_map = self.root / "tier-map.yaml"
        self.tier_map.write_text(TIER_MAP, encoding="utf-8")
        (self.pack / "openup-demo.md").write_text(PROC, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def _args(self, mode):
        return [
            mode,
            "--procedures-dir", str(self.pack),
            "--mirror-dir", str(self.mirror),
            "--tier-map", str(self.tier_map),
        ]

    def _mirror_file(self):
        return self.mirror / "openup-demo" / "SKILL.md"

    def test_write_creates_rendered_mirror(self):
        run(self._args("--write"), expect_code=0)
        self.assertEqual(self._mirror_file().read_text(encoding="utf-8"), EXPECTED)

    def test_check_passes_after_write(self):
        run(self._args("--write"), expect_code=0)
        run(self._args("--check"), expect_code=0)

    def test_check_flags_missing_mirror(self):
        proc = run(self._args("--check"), expect_code=1)
        self.assertIn("missing", proc.stderr)

    def test_check_flags_hand_edited_mirror(self):
        run(self._args("--write"), expect_code=0)
        f = self._mirror_file()
        f.write_text(f.read_text(encoding="utf-8") + "\nhand edit\n", encoding="utf-8")
        proc = run(self._args("--check"), expect_code=1)
        self.assertIn("Differs", proc.stderr)

    def test_check_flags_stale_mirror(self):
        run(self._args("--write"), expect_code=0)
        stale = self.mirror / "openup-gone" / "SKILL.md"
        stale.parent.mkdir(parents=True)
        stale.write_text(EXPECTED, encoding="utf-8")
        proc = run(self._args("--check"), expect_code=1)
        self.assertIn("stale", proc.stderr)

    def test_write_is_idempotent(self):
        run(self._args("--write"), expect_code=0)
        proc = run(self._args("--write"), expect_code=0)
        self.assertIn("0 updated", proc.stdout)


if __name__ == "__main__":
    unittest.main()
