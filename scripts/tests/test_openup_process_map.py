#!/usr/bin/env python3
"""Hermetic tests for scripts/openup-process-map.py — T-100 schema fields
(requires_input + execution) + backward compatibility.

Run with either:
    python3 -m unittest scripts.tests.test_openup_process_map
    python3 scripts/tests/test_openup_process_map.py

The reader is a hyphenated stdlib script; load it via importlib (the bench-test
precedent). Each test writes a tiny process-map.yaml fixture and parses it — the
shipped map is never touched.
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


MAP = """\
phases:
  inception: [initiate-project, test-solution]
activities:
  initiate-project: { role: analyst, skills: [openup-create-vision], requires_input: { path: docs/inputs/stakeholder-brief.md, describe: "a stakeholder brief" }, execution: direct }
  test-solution:    { role: tester,  skills: [openup-create-test-plan] }
phase_letters:
  inception: I
"""


def _write_map(text):
    d = Path(tempfile.mkdtemp())
    (d / "docs-eng-process").mkdir(parents=True)
    (d / "docs-eng-process" / "process-map.yaml").write_text(text, encoding="utf-8")
    return d


class ParseTest(unittest.TestCase):
    def setUp(self):
        self.root = _write_map(MAP)
        self.mp = pm.load_map(self.root)

    def test_nested_requires_input_parses_to_dict(self):
        act = self.mp["activities"]["initiate-project"]
        self.assertIsInstance(act["requires_input"], dict)
        self.assertEqual(act["requires_input"]["path"],
                         "docs/inputs/stakeholder-brief.md")
        self.assertEqual(act["requires_input"]["describe"], "a stakeholder brief")  # unquoted
        self.assertEqual(act["execution"], "direct")

    def test_activity_query_exposes_fields(self):
        a = pm.activity(self.mp, "initiate-project")
        self.assertEqual(a["execution"], "direct")
        self.assertEqual(a["requires_input"]["path"], "docs/inputs/stakeholder-brief.md")

    def test_defaults_for_activity_without_fields(self):
        a = pm.activity(self.mp, "test-solution")
        self.assertIsNone(a["requires_input"])
        self.assertEqual(a["execution"], "spec-then-execute")

    def test_activities_for_carries_fields(self):
        acts = pm.activities_for(self.mp, "inception")
        by = {a["name"]: a for a in acts}
        self.assertEqual(by["initiate-project"]["execution"], "direct")
        self.assertIsNone(by["test-solution"]["requires_input"])


class ValidateTest(unittest.TestCase):
    def _validate(self, text):
        return pm.validate(pm.load_map(_write_map(text)))

    def test_wellformed_passes(self):
        self.assertEqual(self._validate(MAP), [])

    def test_requires_input_without_path_fails(self):
        bad = MAP.replace(
            "requires_input: { path: docs/inputs/stakeholder-brief.md, describe: \"a stakeholder brief\" }",
            "requires_input: { describe: \"no path\" }")
        probs = self._validate(bad)
        self.assertTrue(any("requires_input" in p and "path" in p for p in probs))

    def test_unknown_execution_fails(self):
        bad = MAP.replace("execution: direct", "execution: sideways")
        probs = self._validate(bad)
        self.assertTrue(any("execution" in p for p in probs))

    def test_direct_requires_exactly_one_skill(self):
        bad = MAP.replace(
            "skills: [openup-create-vision], requires_input",
            "skills: [openup-create-vision, openup-shared-vision], requires_input")
        probs = self._validate(bad)
        self.assertTrue(any("direct" in p and "one skill" in p for p in probs))


class BackwardCompatTest(unittest.TestCase):
    def test_legacy_map_unchanged(self):
        legacy = ("phases:\n  inception: [a]\n"
                  "activities:\n  a: { role: analyst, skills: [openup-create-vision] }\n"
                  "phase_letters:\n  inception: I\n")
        mp = pm.load_map(_write_map(legacy))
        self.assertEqual(pm.validate(mp), [])
        a = pm.activity(mp, "a")
        self.assertEqual(a["role"], "analyst")
        self.assertIsNone(a["requires_input"])
        self.assertEqual(a["execution"], "spec-then-execute")


if __name__ == "__main__":
    unittest.main()
