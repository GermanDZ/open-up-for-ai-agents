#!/usr/bin/env python3
"""Hermetic tests for the cycle engine's Plan Iteration path (T-090).

Run with either:
    python3 -m unittest scripts.tests.test_openup_agent_plan_iteration
    python3 scripts/tests/test_openup_agent_plan_iteration.py

The driver-coupled operations (sub-runs, gates, git-commit, the deterministic
script ops) are injected as callables, so every path is exercised with fakes —
zero network, zero LLM, zero real process scripts.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openup_agent import plan_iteration as pi  # noqa: E402


ACTIVITIES = [
    {"name": "initiate-project", "role": "analyst", "skills": ["openup-create-vision"]},
    {"name": "identify-refine-requirements", "role": "analyst",
     "skills": ["openup-create-use-case", "openup-detail-use-case"]},
    {"name": "ongoing-tasks", "role": "developer", "skills": []},  # no skill → skipped
]


class HelperTest(unittest.TestCase):
    def test_generate_lanes_skips_skill_less_activities(self):
        lanes = pi.generate_lanes(ACTIVITIES)
        self.assertEqual([l["activity"] for l in lanes],
                         ["initiate-project", "identify-refine-requirements"])
        self.assertEqual(lanes[0]["skill"], "openup-create-vision")
        self.assertEqual(lanes[1]["skill"], "openup-create-use-case")  # first skill

    def test_render_instance_is_typed_and_traces_lanes(self):
        text = pi.render_iteration_plan_instance(
            "inception", "I1", ["I1-001", "I1-002"], ["author vision"])
        self.assertIn("type: iteration-plan", text)
        self.assertIn("traces-from: [I1-001, I1-002]", text)
        self.assertIn("## Evaluation Criteria", text)
        self.assertIn("author vision", text)

    def test_iteration_plan_path(self):
        self.assertEqual(pi.iteration_plan_path("inception", "I1").as_posix(),
                         "docs/phases/inception/iteration-I1-plan.md")


class ReadObjectivesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".openup").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, obj):
        (self.root / pi.OBJECTIVES_REL).write_text(json.dumps(obj))

    def test_absent_is_none(self):
        self.assertIsNone(pi.read_objectives(self.root))

    def test_valid(self):
        self._write({"objectives": ["a", "b"], "rationale": "x"})
        self.assertEqual(pi.read_objectives(self.root), ["a", "b"])

    def test_empty_and_overlong_rejected(self):
        self._write({"objectives": []})
        self.assertIsNone(pi.read_objectives(self.root))
        self._write({"objectives": ["1", "2", "3", "4", "5", "6"]})
        self.assertIsNone(pi.read_objectives(self.root))

    def test_malformed_is_none(self):
        (self.root / pi.OBJECTIVES_REL).write_text("{nope")
        self.assertIsNone(pi.read_objectives(self.root))


class RunPlanIterationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".openup").mkdir()
        self.commits = []
        self.gate_ok = True

    def tearDown(self):
        self.tmp.cleanup()

    def _ops(self, **over):
        reserved = iter(["I1-001", "I1-002", "I1-003", "I1-004"])

        def dispatch_objectives(instruction, system_prompt):
            (self.root / pi.OBJECTIVES_REL).write_text(
                json.dumps({"objectives": ["author the vision"], "rationale": "r"}))
            return 0

        def dispatch_spec(lane_id, instruction):
            d = self.root / "docs" / "changes" / lane_id
            d.mkdir(parents=True, exist_ok=True)
            (d / "plan.md").write_text(
                "---\nid: %s\nstatus: ready\n---\n# %s\n" % (lane_id, lane_id))
            return 0

        ops = dict(
            dispatch_objectives=dispatch_objectives,
            dispatch_spec=dispatch_spec,
            run_gates=lambda: (self.gate_ok, "" if self.gate_ok else "gate boom"),
            git_commit=lambda paths, msg: self.commits.append((tuple(paths), msg)),
            mint_id=lambda ph: "I1",
            activities_for=lambda ph: ACTIVITIES,
            reserve_id=lambda prefix, sess: prefix + next(reserved).split("-")[-1],
            partition=lambda cands: [[c["id"] for c in cands]],
            roadmap_pending=lambda: ["Feature A"],
            lifecycle=lambda: {"phase": "inception", "milestone": "LCO", "criteria": []},
        )
        ops.update(over)
        return ops

    def _run(self, phase="inception", **over):
        return pi.run_plan_iteration(self.root, phase, **self._ops(**over))

    # -- T-101: map-driven input gate + execution:direct --------------------
    _DIRECT_ACTS = [{"name": "initiate-project", "role": "analyst",
                     "skills": ["openup-create-vision"], "execution": "direct",
                     "requires_input": {"path": "docs/inputs/brief.md",
                                        "describe": "a stakeholder brief"}}]

    def test_missing_input_scaffolds_and_suspends_before_minting(self):
        minted = []
        rc = self._run(activities_for=lambda ph: self._DIRECT_ACTS,
                       mint_id=lambda ph: minted.append(ph) or "I1",
                       run_procedure=lambda *a: self.fail("must not run yet"))
        self.assertEqual(rc, pi.PI_SUSPEND)
        brief = self.root / "docs" / "inputs" / "brief.md"
        self.assertTrue(brief.exists())
        self.assertIn(pi.INPUT_TEMPLATE_MARKER, brief.read_text())
        self.assertEqual(minted, [])        # never minted
        self.assertEqual(self.commits, [])  # authored nothing

    def test_direct_activity_runs_procedure_no_lane(self):
        brief = self.root / "docs" / "inputs" / "brief.md"
        brief.parent.mkdir(parents=True)
        brief.write_text("# Real brief\nmy product\n")  # present, no marker
        ran = []
        rc = self._run(activities_for=lambda ph: self._DIRECT_ACTS,
                       run_procedure=lambda proc, instr: ran.append(proc) or 0)
        self.assertEqual(rc, pi.PI_OK)
        self.assertEqual(ran, ["openup-create-vision"])
        # no change-folder lane authored for the direct activity
        self.assertFalse((self.root / "docs" / "changes" / "I1-001").exists())
        inst = self.root / "docs/phases/inception/iteration-I1-plan.md"
        self.assertIn("Directly-run activities", inst.read_text())

    def test_direct_without_runner_is_config_error(self):
        brief = self.root / "docs" / "inputs" / "brief.md"
        brief.parent.mkdir(parents=True); brief.write_text("real\n")
        rc = self._run(activities_for=lambda ph: self._DIRECT_ACTS,
                       run_procedure=None)
        self.assertEqual(rc, pi.PI_CONFIG)

    def test_present_input_does_not_scaffold(self):
        brief = self.root / "docs" / "inputs" / "brief.md"
        brief.parent.mkdir(parents=True); brief.write_text("real\n")
        rc = self._run(activities_for=lambda ph: self._DIRECT_ACTS,
                       run_procedure=lambda *a: 0)
        self.assertEqual(rc, pi.PI_OK)  # proceeded, no suspend

    def test_happy_path_plans_two_lanes_and_instance(self):
        rc = self._run()
        self.assertEqual(rc, pi.PI_OK)
        self.assertTrue((self.root / "docs/changes/I1-001/plan.md").exists())
        self.assertTrue((self.root / "docs/changes/I1-002/plan.md").exists())
        inst = self.root / "docs/phases/inception/iteration-I1-plan.md"
        self.assertTrue(inst.exists())
        text = inst.read_text()
        self.assertIn("traces-from: [I1-001, I1-002]", text)
        # commits: 2 lane specs + 1 instance
        self.assertEqual(len(self.commits), 3)
        self.assertIn("iteration-plan instance", self.commits[-1][1])

    def test_non_authoring_phase_not_planned(self):
        self.assertEqual(self._run(phase="construction"), pi.PI_STEP)
        self.assertEqual(self.commits, [])

    def test_objectives_subrun_failure_propagates(self):
        rc = self._run(dispatch_objectives=lambda i, s: pi.PI_STEP)
        self.assertEqual(rc, pi.PI_STEP)
        self.assertEqual(self.commits, [])

    def test_no_objectives_file_aborts(self):
        rc = self._run(dispatch_objectives=lambda i, s: 0)  # writes nothing
        self.assertEqual(rc, pi.PI_STEP)
        self.assertEqual(self.commits, [])

    def test_missing_lane_spec_aborts_before_instance(self):
        rc = self._run(dispatch_spec=lambda lid, ins: 0)  # returns 0 but writes nothing
        self.assertEqual(rc, pi.PI_STEP)
        self.assertFalse((self.root / "docs/phases/inception").exists())

    def test_gate_failure_after_lane_aborts(self):
        self.gate_ok = False
        rc = self._run()
        self.assertEqual(rc, pi.PI_STEP)
        # no instance written
        self.assertFalse((self.root / "docs/phases/inception").exists())

    def test_objectives_suspend_propagates(self):
        rc = self._run(dispatch_objectives=lambda i, s: pi.PI_SUSPEND)
        self.assertEqual(rc, pi.PI_SUSPEND)

    def test_mint_failure_is_config_error(self):
        rc = self._run(mint_id=lambda ph: "")
        self.assertEqual(rc, pi.PI_CONFIG)


if __name__ == "__main__":
    unittest.main()
