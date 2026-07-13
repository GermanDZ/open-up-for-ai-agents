#!/usr/bin/env python3
"""Hermetic tests for the process navigator (T-096).

Run with either:
    python3 -m unittest scripts.tests.test_openup_agent_navigator
    python3 scripts/tests/test_openup_agent_navigator.py

The navigator's two driver-coupled operations (running the judgment sub-run and
running the chosen procedure) are injected as callables, so every path is tested
with fakes — zero network, zero LLM. Facts assembly and the input-request runner
use an injected ``runner`` that dispatches by argv.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openup_agent import navigator  # noqa: E402


def _fact_runner(status=None, activities=None):
    """A facts runner faking lifecycle status + process-map activities-for."""
    status = status or {"phase": "inception", "milestone": "LCO", "criteria": []}
    activities = activities if activities is not None else [
        {"name": "initiate-project", "role": "analyst",
         "skills": ["openup-create-vision"]}]

    def run(root, argv):
        if "openup-lifecycle.py" in argv[0]:
            return 0, json.dumps(status)
        if "openup-process-map.py" in argv[0]:
            return 0, json.dumps(activities)
        return 1, ""
    return run


class BuildInputTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs-eng-process" / "procedures").mkdir(parents=True)
        for n in ("openup-create-vision", "openup-next", "openup-complete-task"):
            (self.root / "docs-eng-process" / "procedures" / (n + ".md")).write_text("x")

    def tearDown(self):
        self.tmp.cleanup()

    def test_assembles_facts_from_scripts_and_filesystem(self):
        (self.root / "docs").mkdir()
        (self.root / "docs" / "roadmap.md").write_text("# Roadmap\n")
        facts = navigator.build_navigator_input(self.root, runner=_fact_runner())
        self.assertEqual(facts["phase"], "inception")
        self.assertEqual(facts["phase_activities"][0]["skills"], ["openup-create-vision"])
        self.assertTrue(facts["ring1_artifacts"]["roadmap"])
        self.assertFalse(facts["ring1_artifacts"]["vision"])
        self.assertIn("openup-create-vision", facts["procedures_index"])
        self.assertIn("openup-next", facts["procedures_index"])

    def test_survey_reports_absent_artifacts(self):
        facts = navigator.build_navigator_input(self.root, runner=_fact_runner())
        self.assertFalse(any(facts["ring1_artifacts"].values()))


class ReadDecisionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".openup").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, obj):
        (self.root / navigator.DECISION_REL).write_text(json.dumps(obj))

    def test_absent_file_is_none(self):
        self.assertIsNone(navigator.read_navigator_decision(self.root))

    def test_malformed_is_none(self):
        (self.root / navigator.DECISION_REL).write_text("{not json")
        self.assertIsNone(navigator.read_navigator_decision(self.root))

    def test_valid_procedure_decision(self):
        self._write({"procedure": "openup-create-vision",
                     "instruction": "read the brief", "missing_inputs": [],
                     "rationale": "fresh"})
        d = navigator.read_navigator_decision(self.root)
        self.assertEqual(d["procedure"], "openup-create-vision")
        self.assertEqual(d["instruction"], "read the brief")
        self.assertEqual(d["missing_inputs"], [])

    def test_null_procedure_and_missing_inputs_normalized(self):
        self._write({"procedure": None, "instruction": "",
                     "missing_inputs": ["a brief", "  ", ""], "rationale": ""})
        d = navigator.read_navigator_decision(self.root)
        self.assertIsNone(d["procedure"])
        self.assertEqual(d["missing_inputs"], ["a brief"])

    def test_bad_types_rejected(self):
        self._write({"procedure": 5, "missing_inputs": []})
        self.assertIsNone(navigator.read_navigator_decision(self.root))


class RunNavigatorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".openup").mkdir()
        (self.root / "docs-eng-process" / "procedures").mkdir(parents=True)
        self.logs = []
        self.printed = []

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, dispatch, run_procedure, runner=None):
        return navigator.run_navigator(
            self.root, dispatch=dispatch, run_procedure=run_procedure,
            runner=runner or _fact_runner(),
            log=self.logs.append, print_=self.printed.append)

    def _writes_decision(self, obj):
        """A dispatch that emulates the sub-run writing the decision file."""
        def dispatch(instruction, system_prompt):
            (self.root / navigator.DECISION_REL).write_text(json.dumps(obj))
            return 0
        return dispatch

    def test_process_artifact_procedure_runs_directly(self):
        ran = {}

        def run_procedure(procedure, instruction):
            ran["procedure"] = procedure
            ran["instruction"] = instruction
            return 0
        rc = self._run(
            self._writes_decision({"procedure": "openup-create-vision",
                                   "instruction": "author vision",
                                   "missing_inputs": [], "rationale": "fresh"}),
            run_procedure)
        self.assertEqual(rc, 0)
        self.assertEqual(ran["procedure"], "openup-create-vision")
        self.assertEqual(ran["instruction"], "author vision")

    def test_missing_input_raises_request_and_suspends(self):
        # runner also fakes openup-input.py request -> writes a file.
        def runner(root, argv):
            if "openup-input.py" in argv[0]:
                d = Path(root) / "docs" / "input-requests"
                d.mkdir(parents=True, exist_ok=True)
                p = d / "req-1.md"
                p.write_text("status: pending\n")
                return 0, json.dumps({"request": "docs/input-requests/req-1.md"})
            return _fact_runner()(root, argv)
        rc = self._run(
            self._writes_decision({"procedure": None, "instruction": "",
                                   "missing_inputs": ["a stakeholder brief"],
                                   "rationale": "no product input"}),
            lambda *a: self.fail("must not run a procedure"),
            runner=runner)
        self.assertEqual(rc, navigator.NAV_SUSPEND)
        self.assertTrue(self.printed[-1].startswith("OPENUP-AGENT: SUSPENDED"))
        self.assertTrue((self.root / "docs" / "input-requests" / "req-1.md").exists())

    def test_open_request_re_suspends_without_duplicating(self):
        # Pre-seed an open request recorded in cycle meta.
        d = self.root / "docs" / "input-requests"
        d.mkdir(parents=True)
        (d / "req-1.md").write_text("status: pending\n")
        navigator._write_nav_meta(self.root, request="docs/input-requests/req-1.md")
        created = []

        def runner(root, argv):
            if "openup-input.py" in argv[0]:
                created.append(argv)
                return 0, json.dumps({"request": "docs/input-requests/req-2.md"})
            return _fact_runner()(root, argv)
        rc = self._run(
            self._writes_decision({"procedure": None, "instruction": "",
                                   "missing_inputs": ["still need a brief"],
                                   "rationale": "x"}),
            lambda *a: self.fail("no procedure"), runner=runner)
        self.assertEqual(rc, navigator.NAV_SUSPEND)
        self.assertEqual(created, [])  # did NOT create a second request

    def test_null_procedure_no_missing_is_done(self):
        rc = self._run(
            self._writes_decision({"procedure": None, "instruction": "",
                                   "missing_inputs": [], "rationale": "complete"}),
            lambda *a: self.fail("no procedure"))
        self.assertEqual(rc, navigator.NAV_OK)
        self.assertTrue(self.printed[-1].startswith("OPENUP-NEXT: DONE"))

    def test_non_process_artifact_procedure_deferred_to_consent(self):
        rc = self._run(
            self._writes_decision({"procedure": "openup-plan-feature",
                                   "instruction": "add scope",
                                   "missing_inputs": [], "rationale": "x"}),
            lambda *a: self.fail("product-scope work must not run directly"))
        self.assertEqual(rc, navigator.NAV_OK)
        self.assertTrue(any("consent gate" in m for m in self.printed))

    def test_no_decision_file_is_step_error(self):
        rc = self._run(lambda i, s: 0,  # dispatch writes nothing
                       lambda *a: self.fail("no procedure"))
        self.assertEqual(rc, navigator.NAV_STEP)

    def test_failed_subrun_propagates(self):
        rc = self._run(lambda i, s: navigator.NAV_CONFIG,
                       lambda *a: self.fail("no procedure"))
        self.assertEqual(rc, navigator.NAV_CONFIG)

    def test_suspended_subrun_propagates(self):
        rc = self._run(lambda i, s: navigator.NAV_SUSPEND,
                       lambda *a: self.fail("no procedure"))
        self.assertEqual(rc, navigator.NAV_SUSPEND)


if __name__ == "__main__":
    unittest.main()
