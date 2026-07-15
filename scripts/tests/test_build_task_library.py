#!/usr/bin/env python3
"""Hermetic tests for scripts/build-task-library.py (T-105).

Run with either:
    python3 -m unittest scripts.tests.test_build_task_library
    python3 scripts/tests/test_build_task_library.py

Covers Stage-1 extraction from a KB fixture, --offline prompt emission, and
--check drift detection. No network: the LLM path is never exercised here (that
is compile-time, human-reviewed). Fixtures build a tiny repo skeleton with a
synthetic KB task file + a task-library.yaml pointing at it.
"""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO / "scripts" / "build-task-library.py"
_spec = importlib.util.spec_from_file_location("build_task_library", _SCRIPT)
btl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(btl)

# A synthetic KB task file with the UMA-regular structure the extractor parses.
_KB = """\
---
title: Plan Iteration
type: Task
uma_name: plan_iteration
related:
  roles:
  - project-manager-4
  - analyst-6
---

Intro line.
---

Relationships

Roles| Primary Performer:
  * [Project Manager](x.md)
---|---|---
Inputs| Mandatory:
  * [Work Items List](a.md)

| Optional:
  * [Risk List](b.md)

Outputs|
  * [Iteration Plan](c.md)

Steps

Do a thing | prose here.
---
"""

_LIB = """\
tasks:
  plan-iteration:
    name: Plan Iteration
    role: project-manager
    artifact: iteration-plan
    output_path: docs/iteration-plans/iteration-plan.md
    source: kb/plan-iteration.md
    inputs:
      - Work Items List
      - Risk List
    judgment:
      - States the iteration objectives.
      - Selects work items from the top of the list.
      - Defines evaluation criteria.
  author-initial-roadmap:
    name: Author Initial Roadmap
    role: project-manager
    artifact: work-item
    output_path: docs/roadmap.md
    source: driver
    inputs: []
    judgment:
      - Emits a single Markdown table.
      - Task ids are sequential.
      - Every status is pending.
"""


def _mk_repo() -> Path:
    root = Path(tempfile.mkdtemp())
    (root / "docs-eng-process").mkdir()
    (root / "kb").mkdir()
    (root / "kb" / "plan-iteration.md").write_text(_KB, encoding="utf-8")
    (root / "docs-eng-process" / "task-library.yaml").write_text(_LIB, encoding="utf-8")
    return root


class ExtractTests(unittest.TestCase):
    def test_skeleton_fields(self):
        sk = btl.extract_skeleton(_KB)
        self.assertEqual(sk["name"], "Plan Iteration")
        self.assertEqual(sk["role"], "project-manager")  # primary performer, -N stripped
        self.assertEqual(sk["inputs"], ["Work Items List", "Risk List"])

    def test_none_input_skipped(self):
        kb = _KB.replace("  * [Work Items List](a.md)", "  * None")
        self.assertEqual(btl.extract_skeleton(kb)["inputs"], ["Risk List"])


class CheckTests(unittest.TestCase):
    def test_in_sync(self):
        drift, msgs = btl.check_drift(_mk_repo())
        self.assertEqual(drift, 0, msgs)

    def test_detects_mutated_skeleton(self):
        root = _mk_repo()
        lib = root / "docs-eng-process" / "task-library.yaml"
        lib.write_text(lib.read_text().replace("role: project-manager\n    artifact",
                                               "role: analyst\n    artifact", 1),
                       encoding="utf-8")
        drift, msgs = btl.check_drift(root)
        self.assertGreaterEqual(drift, 1)
        self.assertTrue(any(".role" in m for m in msgs))

    def test_driver_def_skipped(self):
        # author-initial-roadmap has source: driver — no KB skeleton, never drifts.
        drift, msgs = btl.check_drift(_mk_repo())
        self.assertFalse(any("author-initial-roadmap" in m for m in msgs))


class OfflineTests(unittest.TestCase):
    def test_offline_emits_prompts_no_network(self):
        root = _mk_repo()
        out = root / "prompts"
        rc = btl.main(["--repo-root", str(root), "--offline", str(out)])
        self.assertEqual(rc, 0)
        # One prompt for the KB-sourced task; none for the driver-native one.
        self.assertTrue((out / "plan-iteration.prompt.txt").exists())
        self.assertFalse((out / "author-initial-roadmap.prompt.txt").exists())
        body = (out / "plan-iteration.prompt.txt").read_text()
        self.assertIn("judgment bullets", body)


class CliCheckTests(unittest.TestCase):
    def test_check_subprocess_in_sync(self):
        root = _mk_repo()
        p = subprocess.run([sys.executable, str(_SCRIPT), "--repo-root", str(root), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_shipped_library_check_in_sync(self):
        p = subprocess.run([sys.executable, str(_SCRIPT), "--check"],
                           capture_output=True, text=True, cwd=str(_REPO))
        self.assertEqual(p.returncode, 0, p.stderr)


if __name__ == "__main__":
    unittest.main()
