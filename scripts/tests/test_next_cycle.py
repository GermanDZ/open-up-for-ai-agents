#!/usr/bin/env python3
"""Hermetic tests for scripts/next-cycle (T-095).

Run with either:
    python3 -m unittest scripts.tests.test_next_cycle
    python3 scripts/tests/test_next_cycle.py

Each test builds a tmp project whose scripts/openup-agent.py is a FAKE that
records its argv + selected env into a log and replays a canned exit code +
stdout from scripts/_agent_behavior.json — so the wrapper's stage detection,
invocation shapes, env plumbing, sentinel passthrough, and exit translation
are all exercised end-to-end through the real executable with zero LLM and
zero engine dependence. The wrapper is run as a subprocess (which also proves
the shebang + non-TTY paths); the interactive env prompt is unit-tested via
importlib against the module's ask seam.
"""

import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_WRAPPER = _REPO / "scripts" / "next-cycle"

_spec = importlib.util.spec_from_file_location(
    "next_cycle", _WRAPPER,
    loader=importlib.machinery.SourceFileLoader("next_cycle", str(_WRAPPER)))
next_cycle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(next_cycle)  # type: ignore[union-attr]

FAKE_AGENT = """\
import json, os, pathlib, sys
pathlib.Path("scripts/_agent_calls.log").open("a").write(json.dumps({
    "argv": sys.argv[1:],
    "LLM_API_URL": os.environ.get("LLM_API_URL"),
}) + "\\n")
beh = {"exit": 0, "stdout": "OPENUP-NEXT: DONE — fake"}
p = pathlib.Path("scripts/_agent_behavior.json")
if p.exists():
    beh.update(json.loads(p.read_text()))
sys.stdout.write(beh["stdout"] + "\\n")
sys.exit(beh["exit"])
"""


class NextCycleFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()
        (self.root / "scripts" / "openup-agent.py").write_text(FAKE_AGENT)
        (self.root / "docs").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _behavior(self, exit=0, stdout="OPENUP-NEXT: DONE — fake"):
        (self.root / "scripts" / "_agent_behavior.json").write_text(
            json.dumps({"exit": exit, "stdout": stdout}))

    def _calls(self):
        p = self.root / "scripts" / "_agent_calls.log"
        if not p.exists():
            return []
        return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

    def _run(self, env_extra=None, with_url=True):
        env = {k: v for k, v in os.environ.items()
               if k not in ("LLM_API_URL", "LLM_API_KEY",
                            "OPENUP_MODEL_MAIN", "OPENUP_MODEL_MID")}
        if with_url:
            env["LLM_API_URL"] = "http://exported/v1"
        env.update(env_extra or {})
        proc = subprocess.run(
            [sys.executable, str(_WRAPPER), "--dir", str(self.root)],
            capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL)
        return proc

    def _mark_started(self):
        (self.root / "docs" / "roadmap.md").write_text("# Roadmap\n")


class EnvTest(NextCycleFixture):
    def test_agent_env_reaches_the_driver(self):
        (self.root / ".openup").mkdir()
        (self.root / ".openup" / "agent.env").write_text(
            "# local endpoint\nLLM_API_URL=http://from-file/v1\n")
        self._mark_started()
        proc = self._run(with_url=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._calls()[0]["LLM_API_URL"], "http://from-file/v1")

    def test_exported_env_wins_over_file(self):
        (self.root / ".openup").mkdir()
        (self.root / ".openup" / "agent.env").write_text(
            "LLM_API_URL=http://from-file/v1\n")
        self._mark_started()
        self._run()  # exported http://exported/v1
        self.assertEqual(self._calls()[0]["LLM_API_URL"], "http://exported/v1")

    def test_missing_env_offtty_guides_and_exits_2(self):
        self._mark_started()
        proc = self._run(with_url=False)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("export LLM_API_URL=", proc.stderr)
        self.assertEqual(self._calls(), [])  # no driver invocation

    def test_interactive_prompt_sets_and_persists(self):
        answers = iter(["http://tty/v1", "k", "main-model", "", "yes"])
        env = {}
        ok = next_cycle.ensure_env(self.root, env, interactive=True,
                                   ask=lambda p: next(answers))
        self.assertTrue(ok)
        self.assertEqual(env["LLM_API_URL"], "http://tty/v1")
        self.assertEqual(env["OPENUP_MODEL_MID"], "main-model")  # empty ⇒ main
        saved = (self.root / ".openup" / "agent.env").read_text()
        self.assertIn("LLM_API_URL=http://tty/v1", saved)


class FreshProjectTest(NextCycleFixture):
    def test_writes_template_brief_and_stops(self):
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        brief = self.root / "docs" / "inputs" / "stakeholder-brief.md"
        self.assertTrue(brief.exists())
        self.assertIn(next_cycle.TEMPLATE_MARKER, brief.read_text())
        self.assertIn("fill in every section", proc.stderr)
        self.assertEqual(self._calls(), [])

    def test_template_brief_not_overwritten(self):
        brief = self.root / "docs" / "inputs" / "stakeholder-brief.md"
        brief.parent.mkdir(parents=True)
        brief.write_text(next_cycle.TEMPLATE_MARKER + "\n# my notes so far\n")
        proc = self._run()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("my notes so far", brief.read_text())  # untouched
        self.assertIn("template marker", proc.stderr)
        self.assertEqual(self._calls(), [])

    def test_filled_brief_runs_inception(self):
        brief = self.root / "docs" / "inputs" / "stakeholder-brief.md"
        brief.parent.mkdir(parents=True)
        brief.write_text("# Brief — RealProduct\nreal content, no marker\n")
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        calls = self._calls()
        self.assertEqual(len(calls), 1)
        argv = calls[0]["argv"]
        self.assertEqual(argv[0], "run")
        self.assertIn("openup-create-vision", argv)
        instruction = argv[argv.index("--instruction") + 1]
        for needle in ("stakeholder-brief.md", "docs/vision.md", "docs/roadmap.md"):
            self.assertIn(needle, instruction)


class CycleStageTest(NextCycleFixture):
    def test_started_project_runs_one_cycle_no_interactive_offtty(self):
        self._mark_started()
        self._behavior(exit=0, stdout="OPENUP-NEXT: ADVANCED — T-002")
        proc = self._run()
        self.assertEqual(proc.returncode, 0)
        calls = self._calls()
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["argv"][0], "cycle")
        self.assertNotIn("--interactive", calls[0]["argv"])

    def test_sentinel_passthrough_and_suspend_guidance(self):
        self._mark_started()
        self._behavior(exit=5, stdout="OPENUP-AGENT: SUSPENDED — docs/input-requests/r.md")
        proc = self._run()
        self.assertEqual(proc.returncode, 5)
        self.assertIn("OPENUP-AGENT: SUSPENDED — docs/input-requests/r.md",
                      proc.stdout)                      # stdout verbatim
        self.assertIn("status: answered", proc.stderr)  # ...guidance on stderr
        self.assertIn("re-run", proc.stderr)

    def test_advanced_suggests_running_again(self):
        self._mark_started()
        self._behavior(exit=0, stdout="OPENUP-NEXT: ADVANCED — T-002")
        proc = self._run()
        self.assertIn("run ./scripts/next-cycle again", proc.stderr)

    def test_every_typed_exit_has_guidance(self):
        self._mark_started()
        for code in (2, 3, 4, 6, 7, 8):
            with self.subTest(code=code):
                self._behavior(exit=code, stdout="")
                proc = self._run()
                self.assertEqual(proc.returncode, code)
                # some guidance beyond the driver's own output
                self.assertIn("[next-cycle]", proc.stderr)

    def test_not_a_project_exits_2(self):
        proc = subprocess.run(
            [sys.executable, str(_WRAPPER), "--dir", self.tmp.name + "/nowhere"],
            capture_output=True, text=True, stdin=subprocess.DEVNULL)
        self.assertEqual(proc.returncode, 2)


class ShippedTest(unittest.TestCase):
    def test_manifest_install_lands_executable_with_shebang(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "scripts"
            proc = subprocess.run(
                ["bash", "-c",
                 'source "%s/scripts/lib/install-process-clis.sh" && '
                 'install_process_clis "%s/scripts" "%s" false false'
                 % (_REPO, _REPO, dest)],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            wrapper = dest / "next-cycle"
            self.assertTrue(wrapper.exists())
            self.assertTrue(wrapper.stat().st_mode & stat.S_IXUSR)
            self.assertTrue(wrapper.read_text().startswith("#!/usr/bin/env python3"))


if __name__ == "__main__":
    unittest.main()
