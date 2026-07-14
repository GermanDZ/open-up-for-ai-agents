#!/usr/bin/env python3
"""Hermetic tests for the deterministic cycle engine (T-089).

Run with either:
    python3 -m unittest scripts.tests.test_openup_agent_cycle
    python3 scripts/tests/test_openup_agent_cycle.py

Each test builds an isolated tmp OpenUP project whose composed process scripts
(board / session / state / sync-status / gates) are tiny FAKES the test
controls, plus a real `git init` repo — so every engine decision path, the
step executor, and the completion ceremony are exercised with zero network and
zero dependence on the real process scripts' internals (those have their own
suites). The judgment sub-run is driven either through the `_subrun` seam
(engine-level assertions) or the loop's scripted `_completion` seam (whole
sub-run path incl. tools + gates).
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openup_agent import cycle  # noqa: E402


TIER_MAP = """\
driver:
  authoring: "${OPENUP_MODEL_MID:-local-mid}"
"""

# -- fake composed scripts ---------------------------------------------------
# Dynamic: a READY change-folder lane wins (so a recovery round's re-resolve
# sees the repo change); otherwise the canned scripts/_decision.json decision.
FAKE_BOARD = """\
import json, pathlib, sys
changes = pathlib.Path("docs/changes")
if changes.is_dir():
    for plan in sorted(changes.glob("*/plan.md")):
        txt = plan.read_text()
        if "status: ready" in txt:
            tid = plan.parent.name
            print(json.dumps({"path": "pick",
                              "lane": {"task": tid, "track": "quick"},
                              "resumable_input": None, "active_iteration": None,
                              "phase": "construction", "cycle": 1,
                              "legacy_path": None, "reason": "ready lane " + tid}))
            sys.exit(0)
print(pathlib.Path("scripts/_decision.json").read_text())
"""

FAKE_SESSION = """\
import json, pathlib, sys
argv = sys.argv[1:]
pathlib.Path("scripts/_calls.log").open("a").write("session:" + " ".join(argv) + "\\n")
if argv and argv[0] == "begin":
    task = argv[argv.index("--task-id") + 1]
    track = argv[argv.index("--track") + 1]
    p = pathlib.Path(".openup"); p.mkdir(exist_ok=True)
    (p / "state.json").write_text(json.dumps({"task_id": task, "track": track}))
elif argv and argv[0] == "end":
    dest = pathlib.Path(argv[argv.index("--archive-to") + 1])
    sp = pathlib.Path(".openup/state.json")
    if sp.exists():
        dest.write_text(sp.read_text())
        sp.unlink()
sys.exit(0)
"""

FAKE_STATE = """\
import pathlib, sys
pathlib.Path("scripts/_calls.log").open("a").write("state:" + " ".join(sys.argv[1:]) + "\\n")
sys.exit(0)
"""

FAKE_SYNC = """\
import pathlib, sys
pathlib.Path("scripts/_calls.log").open("a").write("sync-status\\n")
sys.exit(0)
"""

# gates: fail while a block-file exists (mirrors test_openup_agent.py)
FAKE_FENCE = """\
import os, sys
sys.exit(1 if os.path.exists(".fence_block") else 0)
"""

FAKE_CHECK_DOCS = """\
import os, sys
sys.exit(1 if os.path.exists(".docs_block") else 0)
"""

# T-094 fakes: a request creator writing the real frontmatter shape, and a
# roadmap `next` that is promotable iff the roadmap carries the marker row.
FAKE_INPUT = """\
import argparse, json, pathlib, sys
ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd")
req = sub.add_parser("request")
req.add_argument("--title"); req.add_argument("--question")
req.add_argument("--option", action="append"); req.add_argument("--json", action="store_true")
req.add_argument("--task-id", default=None); req.add_argument("--root", default=".")
a = ap.parse_args()
d = pathlib.Path("docs/input-requests"); d.mkdir(parents=True, exist_ok=True)
path = d / ("req-%d.md" % (len(list(d.glob("*.md"))) + 1))
opts = "".join("- [ ] `%s`\\n" % o for o in (a.option or []))
path.write_text("---\\ntitle: %s\\nstatus: pending\\n---\\n\\n%s\\n**Question**: %s\\n\\n**Answer**: _(fill in)_\\n" % (a.title, opts, a.question))
print(json.dumps({"request": str(path)}))
"""

FAKE_ROADMAP = """\
import pathlib, sys
rm = pathlib.Path("docs/roadmap.md")
if rm.exists() and "PROMOTABLE" in rm.read_text():
    print('{"id": "T-902"}')
    sys.exit(0)
sys.stderr.write("roadmap exhausted\\n")
sys.exit(3)
"""


def _decision(path, task=None, reason="r", **extra):
    d = {"path": path, "lane": {"task": task} if task else None,
         "resumable_input": None, "active_iteration": None, "phase": "construction",
         "cycle": 1, "legacy_path": None, "reason": reason}
    d.update(extra)
    return d


def _plan(task, boxes, status="ready", track="quick"):
    body = "\n".join("- [%s] %s" % ("x" if done else " ", text)
                     for done, text in boxes)
    return (
        "---\n"
        "id: %s\n"
        "title: cycle test lane\n"
        "status: %s\n"
        "track: %s\n"
        "touches:\n  - docs/scratch/\n"
        "---\n\n"
        "# %s\n\n## Operations\n\n%s\n\n## Norms\n\n- none\n" % (task, status, track, task, body)
    )


def _asst(content=None, tool_calls=None):
    msg = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return {"choices": [{"message": msg}]}


def _tool_call(cid, name, args):
    return {"id": cid, "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}}


class CycleFixture(unittest.TestCase):
    TASK = "T-900"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()
        (self.root / "docs-eng-process").mkdir()
        (self.root / "docs-eng-process" / "tier-map.yaml").write_text(TIER_MAP)
        for name, body in [
            ("openup-board.py", FAKE_BOARD),
            ("openup-session.py", FAKE_SESSION),
            ("openup-state.py", FAKE_STATE),
            ("sync-status.py", FAKE_SYNC),
            ("openup-fence.py", FAKE_FENCE),
            ("check-docs.py", FAKE_CHECK_DOCS),
            ("openup-input.py", FAKE_INPUT),
            ("openup-roadmap.py", FAKE_ROADMAP),
        ]:
            (self.root / "scripts" / name).write_text(body)
        (self.root / ".gitignore").write_text(".openup/\nscripts/_calls.log\n")
        self._git("init", "-b", "main")
        self._git("config", "user.email", "t@example.com")
        self._git("config", "user.name", "t")
        self._git("add", "-A")
        self._git("commit", "-m", "seed", "-q")
        self.env = {"LLM_API_URL": "http://unused.local/v1", "LLM_API_KEY": "k",
                    "OPENUP_MODEL_MID": "mid-model"}

    def tearDown(self):
        self.tmp.cleanup()

    def _git(self, *args):
        subprocess.run(["git"] + list(args), cwd=str(self.root), check=True,
                       capture_output=True, text=True)

    def _seed_lane(self, boxes, task=None, decision_path="pick"):
        task = task or self.TASK
        lane_dir = self.root / "docs" / "changes" / task
        lane_dir.mkdir(parents=True, exist_ok=True)
        (lane_dir / "plan.md").write_text(_plan(task, boxes))
        (self.root / "docs" / "changes" / "archive").mkdir(parents=True, exist_ok=True)
        self._set_decision(_decision(decision_path, task=task))
        self._git("add", "-A")
        self._git("commit", "-m", "lane", "-q")
        return lane_dir / "plan.md"

    def _set_decision(self, decision):
        (self.root / "scripts" / "_decision.json").write_text(json.dumps(decision))

    def _calls(self):
        p = self.root / "scripts" / "_calls.log"
        return p.read_text().splitlines() if p.exists() else []

    def _plan_text(self, task=None, archived=False):
        task = task or self.TASK
        sub = "archive/%s" % task if archived else task
        return (self.root / "docs" / "changes" / sub / "plan.md").read_text()


class DecisionDispatchTest(CycleFixture):
    def test_noop_prints_done_sentinel(self):
        self._set_decision(_decision("noop", reason="board empty"))
        self._git("add", "-A"); self._git("commit", "-m", "d", "-q")
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            #  (T-096): assert the bare-DONE baseline; navigation
            # of a noop is covered by NavigatorDispatchTest.
            rc = cycle.run_cycle(str(self.root), env=self.env)
        self.assertEqual(rc, 0)
        self.assertIn("OPENUP-NEXT: DONE — board empty", buf.getvalue())

    def test_unsupported_paths_exit_typed_without_begin(self):
        # T-091: assess-iteration + milestone-review are now handled; only
        # plan-iteration remains unsupported, and only under --no-recover (T-090
        # handles it under recovery). Assess/milestone dispatch is covered by
        # AssessDispatchTest.
        for path in ("plan-iteration",):
            with self.subTest(path=path):
                self._set_decision(_decision(path, task="C3"))
                rc = cycle.run_cycle(str(self.root), env=self.env, recover=False)
                self.assertEqual(rc, cycle.EXIT_UNSUPPORTED)
                # no session begin ran, no state was created
                self.assertFalse(any(l.startswith("session:begin")
                                     for l in self._calls()))
                self.assertFalse((self.root / ".openup" / "state.json").exists())

    def test_noop_prints_done_with_reason(self):
        """T-103: a genuine noop prints DONE with the decision reason (the fresh
        project now resolves to plan-iteration, not noop; the navigator + the
        hardcoded hint were retired)."""
        self._set_decision(_decision("noop", reason="roadmap exhausted"))
        self._git("add", "-A"); self._git("commit", "-m", "d", "-q")
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cycle.run_cycle(str(self.root), env=self.env)
        self.assertEqual(rc, 0)
        self.assertIn("OPENUP-NEXT: DONE — roadmap exhausted", buf.getvalue())

    def test_noop_with_roadmap_has_no_hint(self):
        (self.root / "docs").mkdir(exist_ok=True)
        (self.root / "docs" / "roadmap.md").write_text("# Roadmap\n")
        self._set_decision(_decision("noop", reason="board empty"))
        self._git("add", "-A"); self._git("commit", "-m", "d", "-q")
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            # recover=False: noop-with-roadmap does not ask (T-094 replenish is
            # under recover); it just prints DONE — no hardcoded hint (T-103).
            rc = cycle.run_cycle(str(self.root), env=self.env, recover=False)
        self.assertEqual(rc, 0)
        self.assertNotIn("no docs/roadmap.md", buf.getvalue())

    def test_pick_acquires_via_session_begin_without_llm(self):
        self._seed_lane([(False, "(developer) Write docs/scratch/out.md saying hello")])
        subrun_calls = []

        def subrun(task, box, instruction):
            subrun_calls.append(box["body"])
            out = self.root / "docs" / "scratch"
            out.mkdir(parents=True, exist_ok=True)
            (out / "out.md").write_text("hello\n")
            return 0

        rc = cycle.run_cycle(str(self.root), env=self.env, _subrun=subrun)
        self.assertEqual(rc, 0)
        begin = [l for l in self._calls() if l.startswith("session:begin")]
        self.assertEqual(len(begin), 1)
        self.assertIn("--task-id %s" % self.TASK, begin[0])
        self.assertIn("--track quick", begin[0])  # read from plan frontmatter
        self.assertEqual(subrun_calls,
                         ["Write docs/scratch/out.md saying hello"])


class StepExecutorTest(CycleFixture):
    def test_script_step_runs_as_code_no_llm(self):
        (self.root / "scripts" / "mark-done.py").write_text(
            "import pathlib\n"
            "pathlib.Path('docs/scratch').mkdir(parents=True, exist_ok=True)\n"
            "pathlib.Path('docs/scratch/marker.txt').write_text('done')\n")
        self._seed_lane([(False, "Run python3 scripts/mark-done.py")])

        def subrun(task, box, instruction):  # any LLM use is a failure
            self.fail("script step must not reach the LLM")

        rc = cycle.run_cycle(str(self.root), env=self.env, _subrun=subrun)
        self.assertEqual(rc, 0)
        self.assertEqual(
            (self.root / "docs" / "scratch" / "marker.txt").read_text(), "done")
        self.assertIn("- [x] Run python3 scripts/mark-done.py",
                      self._plan_text(archived=True))

    def test_script_step_failure_exits_8_box_unticked(self):
        (self.root / "scripts" / "boom.py").write_text("import sys; sys.exit(3)\n")
        self._seed_lane([(False, "Run python3 scripts/boom.py")])
        rc = cycle.run_cycle(str(self.root), env=self.env,
                             _subrun=lambda *a: self.fail("no LLM"))
        self.assertEqual(rc, cycle.EXIT_STEP)
        self.assertIn("- [ ] Run python3 scripts/boom.py", self._plan_text())

    def test_judgment_instruction_carries_box_hat_and_briefing(self):
        self._seed_lane([(False, "(tester) Describe the risks in docs/scratch/r.md")])
        seen = {}

        def subrun(task, box, instruction):
            seen["task"], seen["hat"] = task, box["hat"]
            seen["instruction"] = instruction
            (self.root / "docs" / "scratch").mkdir(parents=True, exist_ok=True)
            (self.root / "docs" / "scratch" / "r.md").write_text("risks\n")
            return 0

        rc = cycle.run_cycle(str(self.root), env=self.env, _subrun=subrun)
        self.assertEqual(rc, 0)
        self.assertEqual(seen["task"], self.TASK)
        self.assertEqual(seen["hat"], "tester")
        self.assertIn("Describe the risks in docs/scratch/r.md", seen["instruction"])
        self.assertIn("docs/changes/%s/plan.md" % self.TASK, seen["instruction"])

    def test_gate_failure_exits_6_box_unticked(self):
        self._seed_lane([(False, "(developer) Break the docs check")])

        def subrun(task, box, instruction):
            (self.root / ".docs_block").write_text("")  # gate now fails
            return 0

        rc = cycle.run_cycle(str(self.root), env=self.env, _subrun=subrun)
        self.assertEqual(rc, cycle.EXIT_GATE)
        self.assertIn("- [ ] (developer) Break the docs check", self._plan_text())

    def test_suspend_propagates_exit_5_box_unticked(self):
        self._seed_lane([(False, "(analyst) Ask the human something")])
        rc = cycle.run_cycle(str(self.root), env=self.env,
                             _subrun=lambda *a: cycle.EXIT_SUSPEND)
        self.assertEqual(rc, cycle.EXIT_SUSPEND)
        self.assertIn("- [ ] (analyst) Ask the human something", self._plan_text())

    def test_resume_starts_at_first_unchecked_box(self):
        self._seed_lane([(True, "(developer) Already done earlier"),
                         (False, "(developer) Write docs/scratch/second.md")],
                        decision_path="resume")
        # a live session exists: state.json names the task (as after a crash)
        (self.root / ".openup").mkdir()
        (self.root / ".openup" / "state.json").write_text(
            json.dumps({"task_id": self.TASK, "track": "quick"}))
        worked = []

        def subrun(task, box, instruction):
            worked.append(box["body"])
            (self.root / "docs" / "scratch").mkdir(parents=True, exist_ok=True)
            (self.root / "docs" / "scratch" / "second.md").write_text("2\n")
            return 0

        rc = cycle.run_cycle(str(self.root), env=self.env, _subrun=subrun)
        self.assertEqual(rc, 0)
        self.assertEqual(worked, ["Write docs/scratch/second.md"])
        self.assertFalse(any(l.startswith("session:begin")
                             for l in self._calls()))


class ClassificationTest(unittest.TestCase):
    def _box(self, text):
        boxes = cycle.parse_boxes("## Operations\n\n- [ ] %s\n" % text)
        self.assertEqual(len(boxes), 1)
        return boxes[0]

    def test_plain_python3_command_is_script(self):
        kind, cmd = cycle.classify_box(self._box("Run python3 scripts/sync-status.py"))
        self.assertEqual((kind, cmd), ("script", "python3 scripts/sync-status.py"))

    def test_backticked_git_command_is_script(self):
        kind, cmd = cycle.classify_box(
            self._box("Sweep with `git status --porcelain` before moving on"))
        self.assertEqual((kind, cmd), ("script", "git status --porcelain"))

    def test_bare_script_span_gets_python3(self):
        kind, cmd = cycle.classify_box(
            self._box("Validate via `scripts/check-docs.py --coverage`"))
        self.assertEqual((kind, cmd), ("script", "python3 scripts/check-docs.py --coverage"))

    def test_prose_is_judgment(self):
        kind, cmd = cycle.classify_box(
            self._box("Append the line `bench ok` to docs/bench-scratch/note.md"))
        self.assertEqual((kind, cmd), ("judgment", None))

    def test_judgment_marker_forces_subrun(self):
        kind, cmd = cycle.classify_box(
            self._box("(judgment) Decide whether python3 scripts/x.py is safe"))
        self.assertEqual((kind, cmd), ("judgment", None))

    def test_auto_marker_forces_script(self):
        kind, cmd = cycle.classify_box(self._box("(auto) python3 scripts/x.py --go"))
        self.assertEqual((kind, cmd), ("script", "python3 scripts/x.py --go"))

    def test_role_hat_parsed_and_default(self):
        self.assertEqual(self._box("(tester) verify it")["hat"], "tester")
        self.assertEqual(self._box("just do it")["hat"], "developer")

    def test_ticked_boxes_are_marked_checked(self):
        boxes = cycle.parse_boxes(
            "## Operations\n\n- [x] first\n- [ ] second\n\n## Norms\n\n- [ ] not-a-step\n")
        self.assertEqual([(b["checked"], b["body"]) for b in boxes],
                         [(True, "first"), (False, "second")])


class CompletionTest(CycleFixture):
    def test_full_completion_ceremony_and_sentinel(self):
        self._seed_lane([(False, "(developer) Write docs/scratch/out.md")])

        def subrun(task, box, instruction):
            (self.root / "docs" / "scratch").mkdir(parents=True, exist_ok=True)
            (self.root / "docs" / "scratch" / "out.md").write_text("done\n")
            return 0

        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cycle.run_cycle(str(self.root), env=self.env, _subrun=subrun)
        self.assertEqual(rc, 0)
        # sentinel parity with /openup-next
        self.assertEqual(buf.getvalue().strip().splitlines()[-1],
                         "OPENUP-NEXT: ADVANCED — %s" % self.TASK)
        # lane archived; plan status flipped to done; state archived + removed
        archived = self.root / "docs" / "changes" / "archive" / self.TASK
        self.assertTrue((archived / "plan.md").exists())
        self.assertIn("status: done", (archived / "plan.md").read_text())
        self.assertTrue((archived / "state.json").exists())
        self.assertFalse((self.root / ".openup" / "state.json").exists())
        # completion shard exists and names the engine
        shards = list((self.root / "docs" / "status-notes").glob("*-%s.md" % self.TASK))
        self.assertEqual(len(shards), 1)
        self.assertIn("cycle engine", shards[0].read_text())
        # ceremony order: log-event → set-gate → sync-status → retro → end
        calls = self._calls()
        order = [i for i, l in enumerate(calls) if
                 l.startswith(("state:log-event", "state:set-gate log_written",
                               "sync-status", "state:retro", "session:end"))]
        self.assertEqual(order, sorted(order))
        self.assertTrue(any(l.startswith("session:end") for l in calls))
        # merged back to the starting branch; work visible from main
        head = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                              cwd=str(self.root), capture_output=True, text=True)
        self.assertEqual(head.stdout.strip(), "main")
        self.assertTrue((self.root / "docs" / "scratch" / "out.md").exists())

    def test_scripted_llm_subrun_end_to_end(self):
        """The whole judgment path through loop.run (tools + gates), no seam."""
        self._seed_lane([(False, "(developer) Write docs/scratch/llm.md containing agent-made")])
        turns = {"n": 0}

        def completion(model, messages, tools_):
            self.assertEqual(model, "mid-model")  # authoring tier resolved
            turns["n"] += 1
            if turns["n"] == 1:
                # step system prompt + instruction must frame ONE step
                self.assertIn("ONE step", messages[0]["content"])
                self.assertIn("Write docs/scratch/llm.md", messages[1]["content"])
                return _asst(tool_calls=[_tool_call(
                    "c1", "write_file",
                    {"path": "docs/scratch/llm.md", "content": "agent-made\n"})])
            return _asst("OPENUP-STEP: DONE — wrote the file")

        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cycle.run_cycle(str(self.root), env=self.env, _completion=completion)
        self.assertEqual(rc, 0)
        self.assertEqual((self.root / "docs" / "scratch" / "llm.md").read_text(),
                         "agent-made\n")
        # the sub-run's own sentinel stayed OFF the engine's stdout
        self.assertNotIn("OPENUP-STEP", buf.getvalue())
        self.assertIn("OPENUP-NEXT: ADVANCED", buf.getvalue())



# --------------------------------------------------------------------------
# Recovery mode (T-092)
# --------------------------------------------------------------------------
class RecoveryCaseBTest(CycleFixture):
    """Unclosed-lane reconcile: done-status active folders are closed (zero
    LLM) before the loop plans new work."""

    def _seed_done_lane(self, decision_path="noop"):
        lane_dir = self.root / "docs" / "changes" / self.TASK
        lane_dir.mkdir(parents=True, exist_ok=True)
        (lane_dir / "plan.md").write_text(
            _plan(self.TASK, [(True, "did the thing")], status="done"))
        self._set_decision(_decision(decision_path, reason="nothing pickable"))
        self._git("add", "-A")
        self._git("commit", "-m", "done lane", "-q")

    def _fail_subrun(self, *a):
        self.fail("Case B must never reach the LLM")

    def test_unclosed_lane_closed_zero_llm(self):
        self._seed_done_lane()
        rc = cycle.run_cycle(str(self.root), env=self.env,
                             _subrun=self._fail_subrun)
        self.assertEqual(rc, 0)
        self.assertTrue((self.root / "docs" / "changes" / "archive" /
                         self.TASK / "plan.md").exists())
        log = subprocess.run(["git", "log", "--oneline", "-2"],
                             cwd=str(self.root), capture_output=True, text=True)
        self.assertIn("recovery — close done-but-unclosed lane", log.stdout)

    def test_side_branch_merged_to_trunk(self):
        self._git("checkout", "-b", "feature/old-delivery", "-q")
        self._seed_done_lane()
        rc = cycle.run_cycle(str(self.root), env=self.env,
                             _subrun=self._fail_subrun)
        self.assertEqual(rc, 0)
        head = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                              cwd=str(self.root), capture_output=True, text=True)
        self.assertEqual(head.stdout.strip(), "main")
        # the closed lane is visible from the trunk
        self.assertTrue((self.root / "docs" / "changes" / "archive" /
                         self.TASK / "plan.md").exists())

    def test_dirty_tree_skips_closure(self):
        self._seed_done_lane()
        (self.root / ".gitignore").write_text(".openup/\n# dirty\n")
        rc = cycle.run_cycle(str(self.root), env=self.env,
                             _subrun=self._fail_subrun)
        self.assertEqual(rc, 0)  # noop still prints DONE
        self.assertTrue((self.root / "docs" / "changes" / self.TASK /
                         "plan.md").exists())  # untouched

    def test_no_recover_leaves_lane_untouched(self):
        self._seed_done_lane()
        rc = cycle.run_cycle(str(self.root), env=self.env, recover=False,
                             _subrun=self._fail_subrun)
        self.assertEqual(rc, 0)
        self.assertTrue((self.root / "docs" / "changes" / self.TASK /
                         "plan.md").exists())

    def test_assess_iteration_dispatched_not_case_b(self):
        # T-091: Case B (done-lane reconcile) does not fire for assess-iteration;
        # the decision goes straight to the assess handler.
        self._seed_done_lane(decision_path="assess-iteration")
        hit = {}

        def fake_assess(root, decision):
            hit["yes"] = True
            return 0
        rc = cycle.run_cycle(str(self.root), env=self.env,
                             _subrun=self._fail_subrun, _assess=fake_assess)
        self.assertTrue(hit.get("yes"))
        self.assertEqual(rc, 0)
        self.assertTrue((self.root / "docs" / "changes" / self.TASK /
                         "plan.md").exists())  # no closure side effects


class RecoveryCaseATest(CycleFixture):
    """Missing-spec recovery: one bounded analyst sub-run authors the
    plan-iteration decision's named work item, then the same cycle picks it."""

    NEW = "T-901"

    def _plan_iteration_decision(self, title="Use case outline"):
        d = _decision("plan-iteration", task=self.NEW,
                      reason="plan a construction-phase iteration")
        d["lane"]["title"] = title
        self._set_decision(d)
        self._git("add", "-A")
        self._git("commit", "-m", "decision", "-q")

    def _spec_writing_subrun(self, status="ready", record=None):
        def subrun(task, box, instruction):
            if record is not None:
                record.append({
                    "task": task, "hat": box["hat"], "instruction": instruction,
                    "begun": any(l.startswith("session:begin")
                                 for l in self._calls()),
                })
            lane = self.root / "docs" / "changes" / self.NEW
            lane.mkdir(parents=True, exist_ok=True)
            (lane / "plan.md").write_text(_plan(
                self.NEW, [(False, "Run `git log --oneline -1`")], status=status))
            return 0
        return subrun

    def test_spec_authored_then_same_cycle_delivers(self):
        self._plan_iteration_decision()
        record = []
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cycle.run_cycle(str(self.root), env=self.env,
                                 _subrun=self._spec_writing_subrun(record=record))
        self.assertEqual(rc, 0)
        self.assertEqual(buf.getvalue().strip().splitlines()[-1],
                         "OPENUP-NEXT: ADVANCED — %s" % self.NEW)
        # exactly ONE sub-run (the spec authoring; the lane's box is a script)
        self.assertEqual(len(record), 1)
        self.assertEqual(record[0]["hat"], "analyst")
        self.assertIn(self.NEW, record[0]["instruction"])
        self.assertIn("frontmatter", record[0]["instruction"])
        self.assertIn("Given", record[0]["instruction"])
        self.assertFalse(record[0]["begun"])  # no session before the spec
        # the spec commit landed before the lane was claimed
        log = subprocess.run(["git", "log", "--oneline"],
                             cwd=str(self.root), capture_output=True, text=True)
        self.assertIn("author spec via cycle recovery", log.stdout)
        # and the lane was executed + archived in the same invocation
        self.assertTrue((self.root / "docs" / "changes" / "archive" /
                         self.NEW / "plan.md").exists())

    def test_no_spec_produced_exits_8(self):
        self._plan_iteration_decision()
        rc = cycle.run_cycle(str(self.root), env=self.env,
                             _subrun=lambda *a: 0)  # "succeeds", writes nothing
        self.assertEqual(rc, cycle.EXIT_STEP)
        self.assertFalse(any(l.startswith("session:begin") for l in self._calls()))

    def test_non_advancing_spec_exits_7(self):
        self._plan_iteration_decision()
        rc = cycle.run_cycle(str(self.root), env=self.env,
                             _subrun=self._spec_writing_subrun(status="proposed"))
        self.assertEqual(rc, cycle.EXIT_UNSUPPORTED)
        self.assertFalse(any(l.startswith("session:begin") for l in self._calls()))

    def test_spec_scenarios_gate_blocks(self):
        (self.root / "scripts" / "openup-spec-scenarios.py").write_text(
            "import sys; sys.exit(1)\n")
        self._plan_iteration_decision()
        rc = cycle.run_cycle(str(self.root), env=self.env,
                             _subrun=self._spec_writing_subrun())
        self.assertEqual(rc, cycle.EXIT_STEP)

    def test_no_recover_keeps_typed_exit_7(self):
        self._plan_iteration_decision()
        rc = cycle.run_cycle(str(self.root), env=self.env, recover=False,
                             _subrun=lambda *a: self.fail("no sub-run under --no-recover"))
        self.assertEqual(rc, cycle.EXIT_UNSUPPORTED)
        self.assertFalse((self.root / "docs" / "changes" / self.NEW).exists())



# --------------------------------------------------------------------------
# Consent-gated replenishment (T-094)
# --------------------------------------------------------------------------
class ReplenishmentTest(CycleFixture):
    """Stuck loop (roadmap present, nothing promotable) → ask → PM sub-run."""

    def _stuck(self, roadmap="# Roadmap\n\n(nothing pending)\n"):
        (self.root / "docs").mkdir(exist_ok=True)
        (self.root / "docs" / "roadmap.md").write_text(roadmap)
        self._set_decision(_decision("noop", reason="roadmap exhausted"))
        self._git("add", "-A"); self._git("commit", "-m", "stuck", "-q")

    def _requests(self):
        d = self.root / "docs" / "input-requests"
        return sorted(d.glob("*.md")) if d.is_dir() else []

    def _answer(self, path, answer):
        text = path.read_text().replace("status: pending", "status: answered")
        text = text.replace("**Answer**: _(fill in)_", "**Answer**: %s" % answer)
        path.write_text(text)

    def _run(self, **kw):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cycle.run_cycle(str(self.root), env=self.env, **kw)
        return rc, buf.getvalue()

    # -- Req 1 -------------------------------------------------------------
    def test_stuck_creates_request_and_suspends(self):
        self._stuck()
        rc, out = self._run(_subrun=lambda *a: self.fail("no sub-run before consent"))
        self.assertEqual(rc, cycle.EXIT_SUSPEND)
        self.assertTrue(out.strip().splitlines()[-1].startswith(
            "OPENUP-AGENT: SUSPENDED"))
        self.assertEqual(len(self._requests()), 1)
        self.assertIn("- [ ] `yes`", self._requests()[0].read_text())
        self.assertEqual(
            cycle.read_cycle_meta(self.root)["replenish"]["request"],
            str(self._requests()[0].relative_to(self.root)))

    def test_no_roadmap_hints_instead_of_asking(self):
        self._set_decision(_decision("noop", reason="roadmap exhausted"))
        self._git("add", "-A"); self._git("commit", "-m", "d", "-q")
        # T-103: a fresh noop just prints DONE (hint + navigator retired).
        rc, out = self._run(_subrun=lambda *a: self.fail("no sub-run"))
        self.assertEqual(rc, 0)
        self.assertIn("OPENUP-NEXT: DONE", out)
        self.assertEqual(self._requests(), [])

    def test_no_recover_never_asks(self):
        self._stuck()
        rc, out = self._run(recover=False,
                            _subrun=lambda *a: self.fail("no sub-run"))
        self.assertEqual(rc, 0)
        self.assertIn("OPENUP-NEXT: DONE", out)
        self.assertEqual(self._requests(), [])

    # -- Req 3 -------------------------------------------------------------
    def test_pending_request_never_duplicates(self):
        self._stuck()
        self._run()
        rc, out = self._run()
        self.assertEqual(rc, cycle.EXIT_SUSPEND)
        self.assertEqual(len(self._requests()), 1)
        self.assertIn(str(self._requests()[0].relative_to(self.root)), out)

    # -- Req 2 -------------------------------------------------------------
    def test_interactive_yes_runs_pm_subrun_without_request(self):
        self._stuck()
        seen = []

        def subrun(task, box, instruction):
            seen.append((task, box["hat"]))
            return 0  # changes nothing → acceptance gate fails afterwards

        rc, _ = self._run(interactive=True, _ask=lambda q: "yes", _subrun=subrun)
        self.assertEqual(seen, [("replenish", "product-manager")])
        self.assertEqual(self._requests(), [])   # TTY consent, no request file
        self.assertEqual(rc, cycle.EXIT_STEP)    # unproductive pass fails typed

    def test_interactive_no_declines_cleanly(self):
        self._stuck()
        rc, out = self._run(interactive=True, _ask=lambda q: "no",
                            _subrun=lambda *a: self.fail("declined"))
        self.assertEqual(rc, 0)
        self.assertIn("replenishment declined by human", out)
        self.assertEqual(self._requests(), [])

    # -- Req 5 -------------------------------------------------------------
    def test_answered_no_is_durable(self):
        self._stuck()
        self._run()
        self._answer(self._requests()[0], "no")
        for _ in range(2):
            rc, out = self._run(_subrun=lambda *a: self.fail("declined"))
            self.assertEqual(rc, 0)
            self.assertIn("replenishment declined by human", out)
        self.assertEqual(len(self._requests()), 1)

    # -- Req 4 -------------------------------------------------------------
    def test_answered_yes_replenishes_then_delivers_same_cycle(self):
        self._stuck()
        self._run()
        self._answer(self._requests()[0], "yes")
        hats = []

        def subrun(task, box, instruction):
            hats.append(box["hat"])
            if box["hat"] == "product-manager":
                rm = self.root / "docs" / "roadmap.md"
                rm.write_text(rm.read_text() +
                              "\n| T-902 | New work | PROMOTABLE pending |\n")
                self._set_decision(_decision(
                    "plan-iteration", task="T-902",
                    reason="plan next (T-902)"))
            else:  # analyst: author the spec so the lane becomes pickable
                lane = self.root / "docs" / "changes" / "T-902"
                lane.mkdir(parents=True, exist_ok=True)
                (lane / "plan.md").write_text(_plan(
                    "T-902", [(False, "Run `git log --oneline -1`")]))
            return 0

        rc, out = self._run(_subrun=subrun)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip().splitlines()[-1],
                         "OPENUP-NEXT: ADVANCED — T-902")
        self.assertEqual(hats, ["product-manager", "analyst"])
        log = subprocess.run(["git", "log", "--oneline"], cwd=str(self.root),
                             capture_output=True, text=True).stdout
        lines = log.splitlines()
        replenish = next(i for i, l in enumerate(lines)
                         if "replenish backlog via cycle recovery" in l)
        spec = next(i for i, l in enumerate(lines)
                    if "author spec via cycle recovery" in l)
        self.assertGreater(replenish, spec)  # replenish commit is OLDER

    # -- Req 6 -------------------------------------------------------------
    def test_unproductive_yes_exits_8_uncommitted(self):
        self._stuck()
        self._run()
        self._answer(self._requests()[0], "yes")
        rc, _ = self._run(_subrun=lambda *a: 0)  # changes nothing
        self.assertEqual(rc, cycle.EXIT_STEP)
        log = subprocess.run(["git", "log", "--oneline"], cwd=str(self.root),
                             capture_output=True, text=True).stdout
        self.assertNotIn("replenish backlog", log)


# --------------------------------------------------------------------------
# Process navigator wiring (T-096)

class PlanIterationDispatchTest(CycleFixture):
    """run_cycle routes an authoring-phase plan-iteration to the Plan Iteration
    handler, and a construction-phase one to the single-row promote."""

    def _decide(self, phase, task="I1"):
        d = _decision("plan-iteration", task=task,
                      reason="plan a %s iteration" % phase, phase=phase)
        d["lane"]["title"] = phase
        self._set_decision(d)
        self._git("add", "-A"); self._git("commit", "-m", "d", "-q")

    def test_authoring_phase_invokes_handler_then_picks(self):
        self._decide("inception")
        called = {}

        def fake_pi(root, decision, phase):
            called["phase"] = phase
            # the handler planned a lane; seed it ready + flip the decision to pick
            self._seed_lane([(False, "(developer) Write docs/scratch/o.md hi")],
                            task="I1-001")
            return 0

        def subrun(task, box, instruction):
            out = self.root / "docs" / "scratch"
            out.mkdir(parents=True, exist_ok=True)
            (out / "o.md").write_text("hi\n")
            return 0

        rc = cycle.run_cycle(str(self.root), env=self.env,
                             _plan_iteration=fake_pi, _subrun=subrun)
        self.assertEqual(called.get("phase"), "inception")
        self.assertEqual(rc, 0)

    def test_construction_phase_bypasses_handler(self):
        self._decide("construction", task="T-901")

        def subrun(task, box, instruction):
            # recover_missing_spec path authors the named spec (proposed → the
            # recovery rejects it, returning a typed exit — enough to prove the
            # single-row promote ran and the Plan Iteration handler did not).
            d = self.root / "docs" / "changes" / "T-901"
            d.mkdir(parents=True, exist_ok=True)
            (d / "plan.md").write_text(
                "---\nid: T-901\nstatus: proposed\n---\n# T-901\n")
            return 0

        rc = cycle.run_cycle(
            str(self.root), env=self.env, _subrun=subrun,
            _plan_iteration=lambda *a: self.fail("handler ran for construction"))
        self.assertNotEqual(rc, 0)  # promote rejected the proposed spec


# --------------------------------------------------------------------------
# Assess + milestone wiring (T-091)
# --------------------------------------------------------------------------
class AssessMilestoneDispatchTest(CycleFixture):
    def test_assess_iteration_invokes_handler(self):
        self._set_decision(_decision("assess-iteration", task="I1"))
        self._git("add", "-A"); self._git("commit", "-m", "d", "-q")
        hit = {}

        def fake_assess(root, dec):
            hit["a"] = True
            return 0
        rc = cycle.run_cycle(str(self.root), env=self.env,
                             _assess=fake_assess)
        self.assertTrue(hit.get("a"))
        self.assertEqual(rc, 0)

    def test_milestone_invokes_handler_and_suspends(self):
        self._set_decision(_decision("milestone-review", task="inception"))
        self._git("add", "-A"); self._git("commit", "-m", "d", "-q")
        hit = {}

        def fake_ms(root, dec):
            hit["m"] = True
            return cycle.EXIT_SUSPEND
        rc = cycle.run_cycle(str(self.root), env=self.env,
                             _milestone=fake_ms)
        self.assertTrue(hit.get("m"))
        self.assertEqual(rc, cycle.EXIT_SUSPEND)

    def test_milestone_review_no_longer_unsupported(self):
        # Real handler (no seam): creates a go/no-go request + suspends (exit 5).
        self._set_decision(_decision("milestone-review", task="inception"))
        self._git("add", "-A"); self._git("commit", "-m", "d", "-q")
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cycle.run_cycle(str(self.root), env=self.env)
        self.assertEqual(rc, cycle.EXIT_SUSPEND)
        reqs = list((self.root / "docs" / "input-requests").glob("*.md"))
        self.assertEqual(len(reqs), 1)


# --------------------------------------------------------------------------
# Engine-owned frontmatter stamping on the direct path (T-104)
# --------------------------------------------------------------------------
class StampDirectArtifactTest(unittest.TestCase):
    """The run_procedure seam stamps the direct artifact after a successful
    sub-run, before the gates — the model authored the body only."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="stamp-wire-")
        self.root = Path(self.tmp.name)
        (self.root / "docs").mkdir()
        self.addCleanup(self.tmp.cleanup)

    def test_known_procedure_stamps_its_artifact(self):
        vision = self.root / "docs" / "vision.md"
        vision.write_text("# Product Vision\n\nBody only.\n", encoding="utf-8")
        rc = cycle._stamp_direct_artifact(self.root, "openup-create-vision")
        self.assertEqual(rc, 0)
        text = vision.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\ntype: vision\nid: VIS-001\n"))
        self.assertIn("status: draft", text)
        self.assertIn("# Product Vision\n\nBody only.\n", text)

    def test_unknown_procedure_is_a_noop(self):
        rc = cycle._stamp_direct_artifact(self.root, "openup-create-pr")
        self.assertEqual(rc, 0)

    def test_missing_artifact_file_is_a_noop(self):
        rc = cycle._stamp_direct_artifact(self.root, "openup-create-vision")
        self.assertEqual(rc, 0)

    def test_roadmap_is_never_stamped(self):
        # docs/roadmap.md is a plain derived view — not in PROCEDURE_ARTIFACTS.
        from openup_agent import stamping
        self.assertNotIn(
            "docs/roadmap.md",
            [rel for _, rel in stamping.PROCEDURE_ARTIFACTS.values()])


if __name__ == "__main__":
    unittest.main()
