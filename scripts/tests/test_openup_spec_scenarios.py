#!/usr/bin/env python3
"""Unit tests for scripts/openup-spec-scenarios.py (T-020).

Run with either:
    python3 -m unittest scripts.tests.test_openup_spec_scenarios
    python3 scripts/tests/test_openup_spec_scenarios.py

Hermetic: each test writes an isolated task spec into a temp dir and exercises
the validator through its CLI exactly as /openup-assess-completeness would.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "openup-spec-scenarios.py"

OK, GAP, USAGE = 0, 1, 2


def write_spec(root, *, track=None, requirements="", section_heading="## Requirements"):
    """Create a minimal plan.md with the given frontmatter track + Requirements body."""
    fm = ["id: T-999", "title: fixture", "status: ready"]
    if track is not None:
        fm.append(f"track: {track}")
    text = "\n".join([
        "---", *fm, "---", "",
        "# T-999 — fixture", "",
        section_heading, "",
        requirements, "",
        "## Approach", "", "Some prose.", "",
    ])
    path = root / "plan.md"
    path.write_text(text, encoding="utf-8")
    return path


def run_check(plan_path, *extra):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "check", str(plan_path), *extra],
        capture_output=True, text=True)


REQ_WITH_SCENARIO = (
    "1. The validator exits 0 when every requirement has a scenario.\n"
    "   - **Given** a spec where each requirement carries a scenario "
    "**When** the check runs **Then** it exits 0.\n"
    "2. The validator exits 1 on a missing scenario.\n"
    "   - **Given** a requirement with no scenario **When** the check runs "
    "**Then** it exits 1 and names the requirement.\n"
)

REQ_MULTILINE_SCENARIO = (
    "1. Multi-line scenarios are accepted.\n"
    "   - **Given** a precondition\n"
    "   - **When** an action happens\n"
    "   - **Then** an outcome is observable\n"
)

REQ_ONE_MISSING = (
    "1. This one has a scenario.\n"
    "   - **Given** x **When** y **Then** z\n"
    "2. This one is a vague assertion with no scenario at all.\n"
)


class TestSpecScenarios(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_all_requirements_have_scenarios_passes(self):
        plan = write_spec(self.root, requirements=REQ_WITH_SCENARIO)
        r = run_check(plan)
        self.assertEqual(r.returncode, OK, r.stderr)
        self.assertIn("all 2 requirement", r.stdout)

    def test_multiline_scenario_accepted(self):
        plan = write_spec(self.root, requirements=REQ_MULTILINE_SCENARIO)
        r = run_check(plan)
        self.assertEqual(r.returncode, OK, r.stderr)

    def test_missing_scenario_fails_and_names_requirement(self):
        plan = write_spec(self.root, requirements=REQ_ONE_MISSING)
        r = run_check(plan)
        self.assertEqual(r.returncode, GAP)
        # Only requirement 2 is flagged, not requirement 1.
        self.assertIn("1 of 2 requirement", r.stderr)
        self.assertIn("2. This one is a vague assertion", r.stderr)
        self.assertNotIn("1. This one has a scenario", r.stderr)

    def test_quick_track_frontmatter_is_skipped(self):
        plan = write_spec(self.root, track="quick", requirements=REQ_ONE_MISSING)
        r = run_check(plan)
        self.assertEqual(r.returncode, OK, r.stderr)
        self.assertIn("exempt", r.stdout)

    def test_quick_track_override_is_skipped(self):
        plan = write_spec(self.root, requirements=REQ_ONE_MISSING)
        r = run_check(plan, "--track", "quick")
        self.assertEqual(r.returncode, OK, r.stderr)

    def test_full_track_frontmatter_is_enforced(self):
        plan = write_spec(self.root, track="full", requirements=REQ_ONE_MISSING)
        r = run_check(plan)
        self.assertEqual(r.returncode, GAP)

    def test_default_track_is_enforced_when_no_frontmatter_track(self):
        plan = write_spec(self.root, requirements=REQ_ONE_MISSING)
        r = run_check(plan)
        self.assertEqual(r.returncode, GAP)

    def test_no_requirements_section_is_usage_error(self):
        plan = write_spec(self.root, requirements="Nothing here.",
                          section_heading="## NotRequirements")
        r = run_check(plan)
        self.assertEqual(r.returncode, USAGE)
        self.assertIn("no '## Requirements'", r.stderr)

    def test_empty_requirements_section_is_gap(self):
        plan = write_spec(self.root, requirements="No numbered items, just prose.")
        r = run_check(plan)
        self.assertEqual(r.returncode, GAP)
        self.assertIn("no numbered requirements", r.stderr)

    def test_missing_file_is_usage_error(self):
        r = run_check(self.root / "does-not-exist.md")
        self.assertEqual(r.returncode, USAGE)

    def test_scenario_does_not_leak_across_requirement_boundary(self):
        # Req 1 holds all three markers; req 2 holds none. The block split must
        # keep req 1's scenario from satisfying req 2.
        reqs = (
            "1. Has a scenario.\n"
            "   - **Given** a **When** b **Then** c\n"
            "2. Has no scenario.\n"
            "3. Also has no scenario.\n"
        )
        plan = write_spec(self.root, requirements=reqs)
        r = run_check(plan)
        self.assertEqual(r.returncode, GAP)
        self.assertIn("2 of 3 requirement", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
