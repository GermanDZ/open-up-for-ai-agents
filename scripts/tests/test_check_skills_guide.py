#!/usr/bin/env python3
"""Unit tests for scripts/check-skills-guide.py.

Run with either:
    python3 -m unittest scripts.tests.test_check_skills_guide
    python3 scripts/tests/test_check_skills_guide.py
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check-skills-guide.py"

DOC_TEMPLATE = """# OpenUP Skills Guide

Hand-written intro that must survive regeneration untouched.

## Skill Reference

<!-- BEGIN GENERATED: skill-reference (scripts/check-skills-guide.py) -->
<!-- END GENERATED: skill-reference -->

## Skill Index

<!-- BEGIN GENERATED: skill-index (scripts/check-skills-guide.py) -->
<!-- END GENERATED: skill-index -->

## References

Hand-written footer.
"""


def run(args, expect_code=None):
    cmd = [sys.executable, str(SCRIPT)] + args
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if expect_code is not None:
        assert proc.returncode == expect_code, (
            f"expected exit {expect_code}, got {proc.returncode}\n"
            f"args={args}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def write_skill(skills_dir, name, *, description="test desc", model="haiku",
                body_extra=""):
    d = skills_dir / name
    d.mkdir(parents=True)
    fm = ["---", f"name: {name}"]
    if description is not None:
        fm.append(f"description: {description}")
    if model is not None:
        fm.append(f"model: {model}")
    fm.append("arguments:")
    fm.append("  - name: foo")
    fm.append("    description: a foo arg")
    fm.append("    required: true")
    fm.append("---")
    text = "\n".join(fm) + f"\n\n# {name}\n{body_extra}\n"
    (d / "SKILL.md").write_text(text, encoding="utf-8")


class LiveRepoTests(unittest.TestCase):
    """The checked-in guide must always be in sync with the checked-in skills."""

    def test_live_repo_is_in_sync(self):
        proc = run(["--check"], expect_code=0)
        self.assertIn("in sync", proc.stdout)


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.skills = self.root / "skills"
        self.skills.mkdir(parents=True)
        self.doc = self.root / "skills-guide.md"
        self.doc.write_text(DOC_TEMPLATE, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def args(self, mode):
        return [mode, "--skills-dir", str(self.skills), "--doc", str(self.doc)]

    def test_write_includes_every_skill_and_preserves_prose(self):
        write_skill(self.skills, "openup-inception")
        write_skill(self.skills, "openup-create-vision")
        write_skill(self.skills, "openup-next")
        run(self.args("--write"), expect_code=0)
        text = self.doc.read_text()
        # All three skills present, grouped correctly.
        self.assertIn("### /openup-inception", text)
        self.assertIn("### /openup-create-vision", text)
        self.assertIn("### /openup-next", text)
        self.assertIn("## Phase Skills", text)
        self.assertIn("## Artifact Skills", text)
        self.assertIn("## Workflow Skills", text)
        # Index row + argument rendering from frontmatter.
        self.assertIn("| `/openup-inception` | Phase | test desc |", text)
        self.assertIn("- `foo` (required) — a foo arg", text)
        # Hand-written prose outside the markers is untouched.
        self.assertIn("Hand-written intro that must survive", text)
        self.assertIn("Hand-written footer.", text)
        run(self.args("--check"), expect_code=0)

    def test_verbatim_body_section_is_lifted(self):
        write_skill(self.skills, "openup-x",
                    body_extra="\n## When to Use\n\n- because reasons\n")
        run(self.args("--write"), expect_code=0)
        text = self.doc.read_text()
        self.assertIn("**When to Use**", text)
        self.assertIn("- because reasons", text)

    def test_check_detects_drift(self):
        write_skill(self.skills, "openup-x")
        run(self.args("--write"), expect_code=0)
        skill = self.skills / "openup-x" / "SKILL.md"
        skill.write_text(skill.read_text().replace("test desc", "changed desc"))
        proc = run(self.args("--check"), expect_code=1)
        self.assertIn("out of sync", proc.stderr)

    def test_new_skill_causes_drift(self):
        write_skill(self.skills, "openup-x")
        run(self.args("--write"), expect_code=0)
        write_skill(self.skills, "openup-y")  # add a skill, don't regenerate
        proc = run(self.args("--check"), expect_code=1)
        self.assertIn("out of sync", proc.stderr)

    def test_missing_description_is_flagged(self):
        write_skill(self.skills, "openup-nodesc", description=None)
        proc = run(self.args("--check"), expect_code=1)
        self.assertIn("missing description/model", proc.stderr)
        self.assertIn("openup-nodesc", proc.stderr)

    def test_quiet_suppresses_success_output(self):
        write_skill(self.skills, "openup-x")
        run(self.args("--write"), expect_code=0)
        proc = run(self.args("--check") + ["--quiet"], expect_code=0)
        self.assertEqual(proc.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
