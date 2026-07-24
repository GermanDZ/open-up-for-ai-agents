#!/usr/bin/env python3
"""Hermetic tests for T-106 activity `tasks:` wiring in the process map.

Run with either:
    python3 -m unittest scripts.tests.test_task_map_wiring
    python3 scripts/tests/test_task_map_wiring.py

Covers: `tasks:` parses onto activity records; `validate` joins them against the
committed task-library ids and rejects an unresolved reference; the shipped map +
library validate clean together.
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

_MAP = """\
phases:
  inception: [initiate-project]
activities:
  initiate-project: { role: analyst, skills: [openup-create-vision], execution: direct, tasks: [develop-technical-vision, author-initial-roadmap] }
phase_letters:
  inception: I
"""


def _load_map(text: str) -> dict:
    root = Path(tempfile.mkdtemp())
    (root / "docs-eng-process").mkdir()
    (root / "docs-eng-process" / "process-map.yaml").write_text(text, encoding="utf-8")
    return pm.load_map(root)


class TasksParseTests(unittest.TestCase):
    def test_tasks_on_activity_record(self):
        mp = _load_map(_MAP)
        rec = pm.activities_for(mp, "inception")[0]
        self.assertEqual(rec["tasks"],
                         ["develop-technical-vision", "author-initial-roadmap"])

    def test_absent_tasks_is_empty_list(self):
        text = _MAP.replace(", tasks: [develop-technical-vision, author-initial-roadmap]", "")
        rec = pm.activities_for(_load_map(text), "inception")[0]
        self.assertEqual(rec["tasks"], [])


class TasksValidateTests(unittest.TestCase):
    def test_unknown_task_id_rejected(self):
        mp = _load_map(_MAP)
        problems = pm.validate(mp, task_ids={"develop-technical-vision"})
        self.assertTrue(any("author-initial-roadmap" in p and "unknown task id" in p
                            for p in problems))

    def test_all_resolved_passes(self):
        mp = _load_map(_MAP)
        ids = {"develop-technical-vision", "author-initial-roadmap"}
        self.assertEqual(pm.validate(mp, task_ids=ids), [])

    def test_no_task_ids_skips_join(self):
        # When the library is absent (task_ids=None), tasks: resolution is not
        # checked — the map still validates structurally.
        self.assertEqual(pm.validate(_load_map(_MAP), task_ids=None), [])


class DirectRequiresTaskTests(unittest.TestCase):
    def test_direct_with_tasks_and_two_skills_passes(self):
        # T-119: direct is task-driven — 2 skills + >=1 task is valid.
        text = _MAP.replace(
            "skills: [openup-create-vision], execution: direct",
            "skills: [openup-create-vision, openup-shared-vision], execution: direct")
        self.assertEqual(pm.validate(_load_map(text)), [])

    def test_direct_without_tasks_fails(self):
        text = _MAP.replace(", tasks: [develop-technical-vision, author-initial-roadmap]", "")
        problems = pm.validate(_load_map(text))
        self.assertTrue(any("direct" in p and "task" in p for p in problems))


class ShippedMapTest(unittest.TestCase):
    def test_shipped_map_and_library_validate_together(self):
        mp = pm.load_map(_REPO)
        ids = set(pm.load_tasks(_REPO))
        self.assertEqual(pm.validate(mp, task_ids=ids), [])


if __name__ == "__main__":
    unittest.main()
