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

    # -- T-101/T-106: map-driven input gate + execution:direct task defs -----
    _DIRECT_ACTS = [{"name": "initiate-project", "role": "analyst",
                     "skills": ["openup-create-vision"], "execution": "direct",
                     "tasks": ["develop-technical-vision", "author-initial-roadmap"],
                     "requires_input": {"path": "docs/inputs/brief.md",
                                        "describe": "a stakeholder brief"}}]

    # T-106: the task library the direct path resolves activity tasks: against.
    _TASK_DEFS = {
        "develop-technical-vision": {
            "name": "Develop Technical Vision", "role": "analyst",
            "artifact": "vision", "output_path": "docs/product/vision.md",
            "source": "kb/vision.md", "inputs": ["Vision"],
            "judgment": ["States the problem before proposing a solution.",
                         "Names the stakeholders and their needs.",
                         "Lists features at capability granularity."]},
        "author-initial-roadmap": {
            "name": "Author Initial Roadmap", "role": "project-manager",
            "artifact": "work-item", "output_path": "docs/roadmap.md",
            "source": "driver", "inputs": [],
            "judgment": ["Header row is exactly `| ID | Title | Status | Priority | Depends on |`.",
                         "Task ids are T-001, T-002, … in sequence.",
                         "Every Status is pending."]},
        "refine-the-architecture": {
            "name": "Refine the Architecture", "role": "architect",
            "artifact": "decision", "output_path": "docs/product/architecture-notebook.md",
            "source": "kb/arch.md", "inputs": ["Architecture Notebook"],
            "judgment": ["Records the key decisions.", "Notes divergences.",
                         "Keeps the significant list current."]},
    }

    def test_missing_input_scaffolds_and_suspends_before_minting(self):
        minted = []
        rc = self._run(activities_for=lambda ph: self._DIRECT_ACTS,
                       mint_id=lambda ph: minted.append(ph) or "I1",
                       task_defs=self._TASK_DEFS,
                       run_task=lambda *a: self.fail("must not run yet"))
        self.assertEqual(rc, pi.PI_SUSPEND)
        brief = self.root / "docs" / "inputs" / "brief.md"
        self.assertTrue(brief.exists())
        self.assertIn(pi.INPUT_TEMPLATE_MARKER, brief.read_text())
        self.assertEqual(minted, [])        # never minted
        self.assertEqual(self.commits, [])  # authored nothing

    def test_direct_activity_runs_ordered_tasks_no_lane(self):
        brief = self.root / "docs" / "inputs" / "brief.md"
        brief.parent.mkdir(parents=True)
        brief.write_text("# Real brief\nmy product\n")  # present, no marker
        ran = []
        rc = self._run(activities_for=lambda ph: self._DIRECT_ACTS,
                       task_defs=self._TASK_DEFS,
                       run_task=lambda tdef, instr: ran.append(tdef["name"]) or 0)
        self.assertEqual(rc, pi.PI_OK)
        # both tasks ran, in the map-declared order (vision then roadmap)
        self.assertEqual(ran, ["Develop Technical Vision", "Author Initial Roadmap"])
        # no change-folder lane authored for the direct activity
        self.assertFalse((self.root / "docs" / "changes" / "I1-001").exists())
        inst = self.root / "docs/phases/inception/iteration-I1-plan.md"
        self.assertIn("Directly-run activities", inst.read_text())

    def test_direct_without_runner_is_config_error(self):
        brief = self.root / "docs" / "inputs" / "brief.md"
        brief.parent.mkdir(parents=True); brief.write_text("real\n")
        rc = self._run(activities_for=lambda ph: self._DIRECT_ACTS,
                       task_defs=self._TASK_DEFS, run_task=None)
        self.assertEqual(rc, pi.PI_CONFIG)

    def test_direct_unknown_task_id_is_config_error(self):
        brief = self.root / "docs" / "inputs" / "brief.md"
        brief.parent.mkdir(parents=True); brief.write_text("real\n")
        rc = self._run(activities_for=lambda ph: self._DIRECT_ACTS,
                       task_defs={}, run_task=lambda *a: 0)  # library empty
        self.assertEqual(rc, pi.PI_CONFIG)

    def test_present_input_does_not_scaffold(self):
        brief = self.root / "docs" / "inputs" / "brief.md"
        brief.parent.mkdir(parents=True); brief.write_text("real\n")
        rc = self._run(activities_for=lambda ph: self._DIRECT_ACTS,
                       task_defs=self._TASK_DEFS, run_task=lambda *a: 0)
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

    # -- T-104/T-106: engine-owned ceremony + task-def instructions ----------
    def _direct_instructions(self, acts=None):
        """Run the direct activity and capture the instruction each task gets."""
        brief = self.root / "docs" / "inputs" / "brief.md"
        brief.parent.mkdir(parents=True, exist_ok=True)
        brief.write_text("real brief\n")
        seen = []
        rc = self._run(activities_for=lambda ph: acts or self._DIRECT_ACTS,
                       task_defs=self._TASK_DEFS,
                       run_task=lambda tdef, instr: seen.append(instr) or 0)
        self.assertEqual(rc, pi.PI_OK)
        return seen

    def test_direct_instruction_excludes_ceremony(self):
        instr = self._direct_instructions()[0]  # the vision task
        self.assertIn("Author the document BODY only", instr)
        for ceremony in ("doc-frontmatter.md", "docs-meta.schema.json",
                         "trace-model.json", "rubric",
                         "docs/project-config.yaml"):
            self.assertIn(ceremony, instr)  # named as prohibited
        self.assertIn("Do NOT self-critique", instr)

    def test_task_instruction_carries_judgment_and_output(self):
        instr = self._direct_instructions()[0]  # the vision task
        self.assertIn("docs/product/vision.md", instr)          # output path
        self.assertIn("States the problem before proposing", instr)  # judgment
        self.assertIn("Vision", instr)                          # workproduct input name kept

    # -- T-118: concrete input path named (kills the glob-thrash) -------------
    def test_task_instruction_names_concrete_input_path(self):
        # _DIRECT_ACTS declares requires_input docs/inputs/brief.md — the task
        # instruction must name that exact path (not only the "Vision" name).
        instr = self._direct_instructions()[0]  # the vision task
        self.assertIn("docs/inputs/brief.md", instr)
        self.assertIn("do not search for it", instr)
        self.assertIn("Vision", instr)  # workproduct name kept as secondary context

    def test_no_requires_input_uses_plain_inputs_line(self):
        # An activity with no requires_input keeps the pre-T-118 "Inputs to read"
        # line and names no phantom path.
        acts = [dict(self._DIRECT_ACTS[0], name="develop-architecture",
                     skills=["openup-create-architecture-notebook"],
                     tasks=["refine-the-architecture"])]
        acts[0].pop("requires_input", None)
        instr = self._direct_instructions(acts)[0]
        self.assertIn("Inputs to read:", instr)
        self.assertNotIn("do not search for it", instr)

    # -- T-120: resolve + inline workproduct-name inputs ---------------------
    def _consumer_def(self, **over):
        d = {"name": "Author Roadmap", "role": "project-manager",
             "artifact": "work-item", "output_path": "docs/roadmap.md",
             "inputs": ["Vision"], "judgment": ["ordered by priority"]}
        d.update(over)
        return d

    def test_task_instruction_resolves_and_inlines_workproduct_input(self):
        # inputs: [Vision] resolves to the vision producer's output_path and
        # inlines its content (Req 2).
        (self.root / "docs" / "product").mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "product" / "vision.md").write_text(
            "# Vision\nBuild the best widget for makers.\n")
        consumer = self._consumer_def()
        lib = dict(self._TASK_DEFS, **{"author-roadmap": consumer})
        instr = pi.render_task_instruction(self.root, consumer, ["ship v1"],
                                           task_defs=lib)
        self.assertIn("docs/product/vision.md", instr)              # resolved path
        self.assertIn("Build the best widget for makers", instr)    # content inlined
        self.assertIn("Vision", instr)                              # display name kept

    def test_task_instruction_absent_input_file_degrades(self):
        # Resolvable name but the file is absent ⇒ no phantom path, no inlined
        # block; the display name stays (Req 2 bullet 2 / Req 6).
        consumer = self._consumer_def()
        lib = dict(self._TASK_DEFS, **{"author-roadmap": consumer})
        instr = pi.render_task_instruction(self.root, consumer, ["ship"],
                                           task_defs=lib)
        self.assertNotIn("already loaded", instr)                   # no inlined block
        self.assertIn("Vision", instr)                              # display name kept

    def test_task_instruction_unresolvable_name_degrades(self):
        # A name with no producer AND no alias (T-124) stays a display name only.
        consumer = self._consumer_def(inputs=["Glossary"])
        lib = dict(self._TASK_DEFS, **{"author-roadmap": consumer})
        instr = pi.render_task_instruction(self.root, consumer, ["x"],
                                           task_defs=lib)
        self.assertNotIn("already loaded", instr)
        self.assertIn("Glossary", instr)

    # -- T-124: alias a non-resolving KB input name to real upstream artifacts --
    def test_task_instruction_aliases_nonresolving_input(self):
        # "Technical Specification" has no producer, but aliases to Vision +
        # Architecture Notebook — both get inlined so the sub-run needs no hunt.
        prod = self.root / "docs" / "product"
        prod.mkdir(parents=True, exist_ok=True)
        (prod / "vision.md").write_text("# Vision\nMakers need a better widget.\n")
        (prod / "architecture-notebook.md").write_text("# Arch\nEvent-driven core.\n")
        consumer = self._consumer_def(inputs=["Technical Specification"])
        lib = dict(self._TASK_DEFS, **{"author-roadmap": consumer})
        instr = pi.render_task_instruction(self.root, consumer, ["ship"],
                                           task_defs=lib)
        self.assertIn("already loaded", instr)                       # a block was inlined
        self.assertIn("Makers need a better widget", instr)          # vision content
        self.assertIn("Event-driven core", instr)                    # architecture content
        self.assertIn("Technical Specification", instr)              # display name kept

    def test_task_instruction_alias_target_absent_degrades(self):
        # aliased, but the alias targets are absent on disk ⇒ no phantom block.
        consumer = self._consumer_def(inputs=["Technical Specification"])
        lib = dict(self._TASK_DEFS, **{"author-roadmap": consumer})
        instr = pi.render_task_instruction(self.root, consumer, ["ship"],
                                           task_defs=lib)
        self.assertNotIn("already loaded", instr)
        self.assertIn("Technical Specification", instr)

    def test_task_instruction_direct_resolve_unchanged_by_alias(self):
        # A directly-resolving name (Vision) still resolves via the producer map,
        # not the alias path — behavior byte-identical to T-120.
        (self.root / "docs" / "product").mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "product" / "vision.md").write_text(
            "# Vision\nBuild the best widget for makers.\n")
        consumer = self._consumer_def()  # inputs: [Vision]
        lib = dict(self._TASK_DEFS, **{"author-roadmap": consumer})
        instr = pi.render_task_instruction(self.root, consumer, ["ship"],
                                           task_defs=lib)
        self.assertIn("Build the best widget for makers", instr)
        self.assertIn("docs/product/vision.md", instr)

    def test_task_instruction_without_library_is_unchanged(self):
        # No task_defs passed ⇒ pre-T-120 behavior (no resolution attempted).
        consumer = self._consumer_def()
        instr = pi.render_task_instruction(self.root, consumer, ["x"])
        self.assertNotIn("already loaded", instr)
        self.assertIn("Vision", instr)

    def test_inline_file_caps_with_path_marker(self):
        (self.root / "big.md").write_text("x" * (pi.INLINE_CAP + 5000))
        block = pi.inline_file(self.root, "big.md", "Big")
        self.assertIn("truncated — full file at `big.md`", block)
        self.assertLess(len(block), pi.INLINE_CAP + 200)

    def test_inline_file_absent_returns_empty(self):
        self.assertEqual(pi.inline_file(self.root, "nope.md", "X"), "")

    # -- T-120: spec lanes carry engine-read vision (read once) --------------
    def _spec_instructions(self):
        seen = []

        def cap(lane_id, instruction):
            seen.append(instruction)
            d = self.root / "docs" / "changes" / lane_id
            d.mkdir(parents=True, exist_ok=True)
            (d / "plan.md").write_text(
                "---\nid: %s\nstatus: ready\n---\n# %s\n" % (lane_id, lane_id))
            return 0

        rc = self._run(dispatch_spec=cap)
        self.assertEqual(rc, pi.PI_OK)
        return seen

    def test_spec_lane_instruction_inlines_vision(self):
        (self.root / "docs" / "product").mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "product" / "vision.md").write_text(
            "# Vision\nEmpower solo makers.\n")
        instrs = self._spec_instructions()
        self.assertTrue(instrs)
        for instr in instrs:                                   # read once, inlined into all
            self.assertIn("Empower solo makers", instr)
            self.assertNotIn("Read docs/vision.md and the Ring-1", instr)

    def test_spec_lane_instruction_degrades_without_vision(self):
        instr = self._spec_instructions()[0]
        self.assertIn("Read docs/vision.md and the Ring-1", instr)

    def test_roadmap_task_carries_pinned_format(self):
        # The pinned roadmap format now lives in the author-initial-roadmap def's
        # judgment (retiring the ROADMAP_FORMAT constant) — it reaches the model
        # through that task's instruction (the second direct task).
        instrs = self._direct_instructions()
        roadmap_instr = instrs[1]
        self.assertIn("| ID | Title | Status | Priority | Depends on |", roadmap_instr)
        self.assertIn("T-001, T-002", roadmap_instr)
        self.assertFalse(hasattr(pi, "ROADMAP_FORMAT"))  # constant retired

    def test_non_roadmap_task_has_no_roadmap_format(self):
        acts = [dict(self._DIRECT_ACTS[0], name="develop-architecture",
                     skills=["openup-create-architecture-notebook"],
                     tasks=["refine-the-architecture"])]
        instr = self._direct_instructions(acts)[0]
        self.assertNotIn("| ID | Title | Status | Priority | Depends on |", instr)

    def test_project_config_injected_when_present(self):
        cfg = self.root / "docs" / "project-config.yaml"
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(
            "context: |\n  Tech stack: python\n  Domain: testing\n"
            "rules:\n  vision:\n    - Name a paying customer\n"
            "  use-case:\n    - Not for visions\n")
        instr = self._direct_instructions()[0]  # the vision task
        self.assertIn("<project-context>", instr)
        self.assertIn("Tech stack: python", instr)
        self.assertIn("<project-rules>", instr)
        self.assertIn("- Name a paying customer", instr)
        self.assertNotIn("Not for visions", instr)  # other artifact's rules

    def test_no_project_config_injects_nothing(self):
        instr = self._direct_instructions()[0]
        self.assertNotIn("<project-context>", instr)
        self.assertNotIn("<project-rules>", instr)

    # -- T-108: direct outputs are gated + committed --------------------------
    def test_direct_success_gates_and_commits_docs(self):
        brief = self.root / "docs" / "inputs" / "brief.md"
        brief.parent.mkdir(parents=True, exist_ok=True)
        brief.write_text("real brief\n")
        rc = self._run(activities_for=lambda ph: self._DIRECT_ACTS,
                       task_defs=self._TASK_DEFS,
                       run_task=lambda tdef, instr: 0)
        self.assertEqual(rc, pi.PI_OK)
        direct = [c for c in self.commits if "initiate-project" in c[1]]
        self.assertEqual(len(direct), 1)  # ONE commit for the whole activity's tasks
        paths, message = direct[0]
        self.assertEqual(paths, ("docs/",))
        self.assertIn("task defs", message)
        self.assertIn("[I1]", message)
        # committed before the iteration-plan instance (the last commit)
        self.assertLess(self.commits.index(direct[0]), len(self.commits) - 1)

    def test_direct_gate_failure_aborts_with_nothing_committed(self):
        brief = self.root / "docs" / "inputs" / "brief.md"
        brief.parent.mkdir(parents=True, exist_ok=True)
        brief.write_text("real brief\n")
        self.gate_ok = False
        rc = self._run(activities_for=lambda ph: self._DIRECT_ACTS,
                       task_defs=self._TASK_DEFS,
                       run_task=lambda tdef, instr: 0)
        self.assertEqual(rc, pi.PI_STEP)
        self.assertEqual(self.commits, [])


class RoadmapFormatContractTest(unittest.TestCase):
    """Regression for the T-103 gap: a roadmap authored exactly per
    ROADMAP_FORMAT must be promotable by the real openup-roadmap.py."""

    def test_format_compliant_roadmap_is_promotable(self):
        import subprocess
        scripts = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "roadmap.md").write_text(
                "# Roadmap\n\n"
                "| ID | Title | Status | Priority | Dependencies | Value |\n"
                "|---|---|---|---|---|---|\n"
                "| T-001 | Foundation | pending | high | none | base |\n"
                "| T-002 | Feature A | pending | medium | T-001 | value |\n")
            proc = subprocess.run(
                [sys.executable, str(scripts / "openup-roadmap.py"), "next",
                 "--root", str(root), "--claims-dir", str(root / "claims"),
                 "--no-remote-check"],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("T-001", proc.stdout)


if __name__ == "__main__":
    unittest.main()
