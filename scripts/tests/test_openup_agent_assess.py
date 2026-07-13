#!/usr/bin/env python3
"""Hermetic tests for the cycle engine's assess + milestone paths (T-091).

Run with either:
    python3 -m unittest scripts.tests.test_openup_agent_assess
    python3 scripts/tests/test_openup_agent_assess.py

The driver-coupled ops (grading sub-run, gates, git-commit, the input-request
runner) are injected as fakes — zero network, zero LLM, zero real scripts.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openup_agent import assess  # noqa: E402


VALID = {
    "criteria": [
        {"criterion": "vision authored", "grade": "met", "evidence": "docs/vision.md"},
        {"criterion": "use-cases done", "grade": "unmet", "evidence": "0 of 2"},
    ],
    "demo": ["I1-001"], "excluded": ["I1-002 — not tested"],
    "discovered": ["defect X"], "verdict": "partially met",
}


class HelperTest(unittest.TestCase):
    def test_render_section_marks_and_verdict(self):
        text = assess.render_assessment_section(_normalize(VALID))
        self.assertIn("## Assessment", text)
        self.assertIn("**Verdict**: partially met", text)
        self.assertIn("✅ vision authored", text)
        self.assertIn("❌ use-cases done", text)
        self.assertIn("### Demo scope", text)
        self.assertIn("defect X", text)


def _normalize(raw):
    """Mirror read_assessment's normalization for a dict fixture."""
    import tempfile as _t
    d = Path(_t.mkdtemp())
    (d / ".openup").mkdir()
    (d / assess.ASSESSMENT_REL).write_text(json.dumps(raw))
    return assess.read_assessment(d)


class ReadAssessmentTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".openup").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, obj):
        (self.root / assess.ASSESSMENT_REL).write_text(json.dumps(obj))

    def test_absent_is_none(self):
        self.assertIsNone(assess.read_assessment(self.root))

    def test_valid_normalizes(self):
        self._write(VALID)
        a = assess.read_assessment(self.root)
        self.assertEqual(len(a["criteria"]), 2)
        self.assertEqual(a["criteria"][0]["grade"], "met")
        self.assertEqual(a["verdict"], "partially met")
        self.assertEqual(a["demo"], ["I1-001"])

    def test_empty_criteria_is_none(self):
        self._write({"criteria": [], "verdict": "x"})
        self.assertIsNone(assess.read_assessment(self.root))

    def test_malformed_is_none(self):
        (self.root / assess.ASSESSMENT_REL).write_text("{nope")
        self.assertIsNone(assess.read_assessment(self.root))


class RunAssessTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".openup").mkdir()
        self.inst_rel = "docs/phases/inception/iteration-I1-plan.md"
        inst = self.root / self.inst_rel
        inst.parent.mkdir(parents=True, exist_ok=True)
        inst.write_text("---\ntype: iteration-plan\nid: IP-I1\n---\n# Iter\n"
                        "## Evaluation Criteria\n- vision authored\n")
        self.commits = []
        self.printed = []
        self.gate_ok = True
        self.decision = {"path": "assess-iteration",
                         "lane": {"task": "I1", "plan": self.inst_rel}}

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, dispatch):
        return assess.run_assess(
            self.root, self.decision, dispatch=dispatch,
            run_gates=lambda: (self.gate_ok, "" if self.gate_ok else "boom"),
            git_commit=lambda paths, msg: self.commits.append((tuple(paths), msg)),
            log=lambda m: None, print_=self.printed.append)

    def _grade(self, obj=VALID):
        def dispatch(instruction, system_prompt):
            (self.root / assess.ASSESSMENT_REL).write_text(json.dumps(obj))
            return 0
        return dispatch

    def test_happy_path_appends_assessment_and_advances(self):
        rc = self._run(self._grade())
        self.assertEqual(rc, assess.AS_OK)
        text = (self.root / self.inst_rel).read_text()
        self.assertIn("## Assessment", text)
        self.assertIn("**Verdict**: partially met", text)
        self.assertEqual(len(self.commits), 1)
        self.assertTrue(self.printed[-1].startswith("OPENUP-NEXT: ADVANCED — assessed I1"))

    def test_missing_instance_is_config_error(self):
        self.decision["lane"]["plan"] = "docs/phases/nope.md"
        self.assertEqual(self._run(self._grade()), assess.AS_CONFIG)

    def test_no_instance_path_is_config_error(self):
        self.decision["lane"].pop("plan")
        self.assertEqual(self._run(self._grade()), assess.AS_CONFIG)

    def test_grading_failure_propagates(self):
        self.assertEqual(self._run(lambda i, s: assess.AS_STEP), assess.AS_STEP)
        self.assertEqual(self.commits, [])

    def test_no_assessment_file_aborts(self):
        rc = self._run(lambda i, s: 0)  # writes nothing
        self.assertEqual(rc, assess.AS_STEP)
        self.assertNotIn("## Assessment", (self.root / self.inst_rel).read_text())

    def test_gate_failure_aborts_without_commit(self):
        self.gate_ok = False
        rc = self._run(self._grade())
        self.assertEqual(rc, assess.AS_STEP)
        self.assertEqual(self.commits, [])


class RunMilestoneTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".openup").mkdir()
        self.printed = []
        self.created = []
        self.decision = {"path": "milestone-review",
                         "lane": {"task": "inception"}, "cycle": 1,
                         "reason": "inception exit criteria met"}

    def tearDown(self):
        self.tmp.cleanup()

    def _runner_ok(self, root, argv):
        # fake openup-input.py request → writes a pending request file
        self.created.append(argv)
        d = Path(root) / "docs" / "input-requests"
        d.mkdir(parents=True, exist_ok=True)
        p = d / ("req-%d.md" % (len(list(d.glob('*.md'))) + 1))
        p.write_text("status: pending\n")
        return 0, json.dumps({"request": str(p.relative_to(root))})

    def _run(self, runner):
        return assess.run_milestone(self.root, self.decision, runner=runner,
                                    log=lambda m: None, print_=self.printed.append)

    def test_creates_request_and_suspends(self):
        rc = self._run(self._runner_ok)
        self.assertEqual(rc, assess.AS_SUSPEND)
        self.assertTrue(self.printed[-1].startswith("OPENUP-AGENT: SUSPENDED"))
        self.assertEqual(len(self.created), 1)
        # GO/NO-GO options were offered
        self.assertIn("GO", " ".join(self.created[0]))

    def test_open_request_re_suspends_without_duplicate(self):
        self._run(self._runner_ok)               # creates req-1
        first = list(self.created)
        rc = self._run(self._runner_ok)          # should re-suspend, not recreate
        self.assertEqual(rc, assess.AS_SUSPEND)
        self.assertEqual(self.created, first)    # no second create
        self.assertFalse((self.root / "docs/input-requests/req-2.md").exists())

    def test_request_creation_failure_is_step(self):
        rc = self._run(lambda r, a: (1, "boom"))
        self.assertEqual(rc, assess.AS_STEP)


if __name__ == "__main__":
    unittest.main()
