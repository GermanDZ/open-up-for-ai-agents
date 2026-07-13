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


# A two-tier fixture tier-map: `fast` -> haiku, `mid` -> sonnet (claude-code
# target). Mirrors docs-eng-process/tier-map.yaml's two-level shape.
TIER_MAP = "claude-code:\n  fast: haiku\n  mid: sonnet\n"


def write_procedure(procedures_dir, name, tier):
    """Write a neutral-pack procedure `openup-<name>.md` with a `tier:` field.

    Post-T-071 skills live in the procedure pack and declare a tier NAME, not a
    concrete model; `tier is None` writes a procedure with no `tier:` line (to
    exercise the missing-field path)."""
    body = "---\nname: openup-%s\n" % name
    if tier is not None:
        body += "tier: %s\n" % tier
    body += "description: test\n---\n\n# openup-%s\n" % name
    (procedures_dir / ("openup-%s.md" % name)).write_text(body, encoding="utf-8")


class LiveRepoTests(unittest.TestCase):
    """The checked-in doc must always be in sync with the checked-in frontmatter."""

    def test_live_repo_is_in_sync(self):
        proc = run(["--check"], expect_code=0)
        self.assertIn("in sync", proc.stdout)


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        # Post-T-071: skills come from the neutral procedure pack (tier: names
        # resolved via a tier-map); agents still carry `model:` in .claude-templates.
        self.templates = self.root / ".claude-templates"
        (self.templates / "agents").mkdir(parents=True)
        self.procedures = self.root / "procedures"
        self.procedures.mkdir(parents=True)
        self.tier_map = self.root / "tier-map.yaml"
        self.tier_map.write_text(TIER_MAP, encoding="utf-8")
        self.doc = self.root / "model-tiers.md"
        self.doc.write_text(DOC_TEMPLATE, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def args(self, mode):
        return [mode,
                "--templates-dir", str(self.templates),
                "--procedures-dir", str(self.procedures),
                "--tier-map", str(self.tier_map),
                "--doc", str(self.doc)]

    def test_write_then_check_roundtrips(self):
        write_procedure(self.procedures, "a", "fast")   # -> haiku
        write_procedure(self.procedures, "b", "mid")    # -> sonnet
        run(self.args("--write"), expect_code=0)
        text = self.doc.read_text()
        # Rows render the RESOLVED model, not the tier name.
        self.assertIn("| openup-a | `haiku` |", text)
        self.assertIn("| openup-b | `sonnet` |", text)
        self.assertIn("1 × `haiku`, 1 × `sonnet` (2 skills).", text)
        # Idempotent: a fresh --check now passes.
        run(self.args("--check"), expect_code=0)

    def test_check_detects_drift(self):
        write_procedure(self.procedures, "a", "fast")
        run(self.args("--write"), expect_code=0)
        # Flip the tier without regenerating the doc -> resolved model changes -> drift.
        proc_file = self.procedures / "openup-a.md"
        proc_file.write_text(proc_file.read_text().replace("tier: fast", "tier: mid"))
        proc = run(self.args("--check"), expect_code=1)
        self.assertIn("out of sync", proc.stderr)

    def test_quiet_suppresses_success_output(self):
        write_procedure(self.procedures, "a", "fast")
        run(self.args("--write"), expect_code=0)
        proc = run(self.args("--check") + ["--quiet"], expect_code=0)
        self.assertEqual(proc.stdout.strip(), "")  # silent on success
        # ...but still reports drift on stderr and exits nonzero.
        proc_file = self.procedures / "openup-a.md"
        proc_file.write_text(proc_file.read_text().replace("tier: fast", "tier: mid"))
        proc = run(self.args("--check") + ["--quiet"], expect_code=1)
        self.assertIn("out of sync", proc.stderr)

    def test_missing_tier_field_is_flagged(self):
        write_procedure(self.procedures, "notier", None)
        proc = run(self.args("--check"), expect_code=1)
        self.assertIn("missing `tier:`", proc.stderr)
        self.assertIn("openup-notier", proc.stderr)

    def test_unknown_tier_name_is_flagged(self):
        write_procedure(self.procedures, "weird", "premium")  # not in tier-map
        proc = run(self.args("--check"), expect_code=1)
        self.assertIn("unknown tier 'premium'", proc.stderr)
        self.assertIn("openup-weird", proc.stderr)


if __name__ == "__main__":
    unittest.main()
