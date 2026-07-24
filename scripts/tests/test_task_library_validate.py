#!/usr/bin/env python3
"""Hermetic tests for the task-library parser + validator (T-105).

Run with either:
    python3 -m unittest scripts.tests.test_task_library_validate
    python3 scripts/tests/test_task_library_validate.py

Each test writes a tiny task-library.yaml fixture and validates it; the shipped
library is exercised separately (it must pass).
"""

import importlib.machinery
import importlib.util
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO / "scripts" / "openup-process-map.py"
_loader = importlib.machinery.SourceFileLoader("openup_process_map", str(_SCRIPT))
_spec = importlib.util.spec_from_file_location("openup_process_map", _SCRIPT, loader=_loader)
pm = importlib.util.module_from_spec(_spec)
_loader.exec_module(pm)

_GOOD = """\
tasks:
  develop-technical-vision:
    name: Develop Technical Vision
    role: analyst
    artifact: vision
    output_path: docs/product/vision.md
    source: kb/vision.md
    inputs:
      - Vision
    judgment:
      - States the problem before proposing a solution.
      - Names the stakeholders and their needs.
      - Lists features at capability granularity.
"""


def _load(text: str) -> dict:
    root = Path(tempfile.mkdtemp())
    (root / "docs-eng-process").mkdir()
    (root / "docs-eng-process" / "task-library.yaml").write_text(text, encoding="utf-8")
    return pm.load_tasks(root)


class ParseTests(unittest.TestCase):
    def test_parses_all_fields(self):
        d = _load(_GOOD)["develop-technical-vision"]
        self.assertEqual(d["name"], "Develop Technical Vision")
        self.assertEqual(d["role"], "analyst")
        self.assertEqual(d["artifact"], "vision")
        self.assertEqual(d["inputs"], ["Vision"])
        self.assertEqual(len(d["judgment"]), 3)

    def test_inline_flow_list_inputs(self):
        text = _GOOD.replace("    inputs:\n      - Vision\n", "    inputs: [Vision, Glossary]\n")
        self.assertEqual(_load(text)["develop-technical-vision"]["inputs"], ["Vision", "Glossary"])


class ValidateTests(unittest.TestCase):
    def test_good_library_passes(self):
        self.assertEqual(pm.validate_tasks(_load(_GOOD)), [])

    def test_missing_field(self):
        text = _GOOD.replace("    role: analyst\n", "")
        problems = pm.validate_tasks(_load(text))
        self.assertTrue(any("missing field 'role'" in p for p in problems))

    def test_bad_artifact_enum(self):
        text = _GOOD.replace("artifact: vision", "artifact: bogus")
        problems = pm.validate_tasks(_load(text))
        self.assertTrue(any("not a spine type" in p for p in problems))

    def test_unknown_role(self):
        text = _GOOD.replace("role: analyst", "role: wizard")
        problems = pm.validate_tasks(_load(text))
        self.assertTrue(any("unknown role" in p for p in problems))

    def test_judgment_too_few(self):
        text = _GOOD.rsplit("      - Lists features at capability granularity.\n", 1)[0]
        text = text.replace("      - Names the stakeholders and their needs.\n", "")
        problems = pm.validate_tasks(_load(text))
        self.assertTrue(any("judgment has" in p for p in problems))

    def test_output_path_not_relative_md(self):
        text = _GOOD.replace("docs/product/vision.md", "/abs/vision.md")
        problems = pm.validate_tasks(_load(text))
        self.assertTrue(any("output_path" in p for p in problems))

    def test_empty_library(self):
        self.assertTrue(any("no tasks" in p for p in pm.validate_tasks({})))


class ShippedLibraryTest(unittest.TestCase):
    def test_committed_library_valid(self):
        self.assertEqual(pm.validate_tasks(pm.load_tasks(_REPO)), [])


if __name__ == "__main__":
    unittest.main()
