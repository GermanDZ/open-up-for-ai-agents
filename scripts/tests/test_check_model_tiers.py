#!/usr/bin/env python3
"""Unit tests for scripts/check-model-tiers.py.

Run with either:
    python3 -m unittest scripts.tests.test_check_model_tiers
    python3 scripts/tests/test_check_model_tiers.py
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check-model-tiers.py"

DOC_TEMPLATE = """# Model Tiers

<!-- BEGIN GENERATED: skill-model-table (scripts/check-model-tiers.py) -->
<!-- END GENERATED: skill-model-table -->

<!-- BEGIN GENERATED: agent-model-table (scripts/check-model-tiers.py) -->
<!-- END GENERATED: agent-model-table -->
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


def write_skill(skills_dir, name, model):
    d = skills_dir / name
    d.mkdir(parents=True)
    body = "---\nname: %s\n" % name
    if model is not None:
        body += "model: %s\n" % model
    body += "description: test\n---\n\n# %s\n" % name
    (d / "SKILL.md").write_text(body, encoding="utf-8")


class LiveRepoTests(unittest.TestCase):
    """The checked-in doc must always be in sync with the checked-in frontmatter."""

    def test_live_repo_is_in_sync(self):
        proc = run(["--check"], expect_code=0)
        self.assertIn("in sync", proc.stdout)


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.templates = self.root / ".claude-templates"
        (self.templates / "skills").mkdir(parents=True)
        (self.templates / "agents").mkdir(parents=True)
        self.doc = self.root / "model-tiers.md"
        self.doc.write_text(DOC_TEMPLATE, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def args(self, mode):
        return [mode, "--templates-dir", str(self.templates), "--doc", str(self.doc)]

    def test_write_then_check_roundtrips(self):
        write_skill(self.templates / "skills", "openup-a", "haiku")
        write_skill(self.templates / "skills", "openup-b", "sonnet")
        run(self.args("--write"), expect_code=0)
        text = self.doc.read_text()
        self.assertIn("| openup-a | `haiku` |", text)
        self.assertIn("| openup-b | `sonnet` |", text)
        self.assertIn("1 × `haiku`, 1 × `sonnet` (2 skills).", text)
        # Idempotent: a fresh --check now passes.
        run(self.args("--check"), expect_code=0)

    def test_check_detects_drift(self):
        write_skill(self.templates / "skills", "openup-a", "haiku")
        run(self.args("--write"), expect_code=0)
        # Flip the frontmatter without regenerating the doc -> drift.
        skill = self.templates / "skills" / "openup-a" / "SKILL.md"
        skill.write_text(skill.read_text().replace("model: haiku", "model: sonnet"))
        proc = run(self.args("--check"), expect_code=1)
        self.assertIn("out of sync", proc.stderr)

    def test_missing_model_field_is_flagged(self):
        write_skill(self.templates / "skills", "openup-nomodel", None)
        proc = run(self.args("--check"), expect_code=1)
        self.assertIn("missing `model:`", proc.stderr)
        self.assertIn("openup-nomodel", proc.stderr)


if __name__ == "__main__":
    unittest.main()
