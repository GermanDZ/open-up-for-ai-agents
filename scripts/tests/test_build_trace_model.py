#!/usr/bin/env python3
"""Unit tests for scripts/build-trace-model.py (T-035).

Run with either:
    python3 -m unittest scripts.tests.test_build_trace_model
    python3 scripts/tests/test_build_trace_model.py

Mixes a hermetic unit layer (synthetic KB manifests exercising the projection /
corroboration logic) with an integration layer that derives the model from the
real vendored KB and asserts the contract the validator depends on.
"""

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "build-trace-model.py"
KB_MANIFEST = SCRIPTS_DIR.parent / "openup-knowledge-base" / "manifest.json"

OK, DRIFT, USAGE = 0, 1, 2


def _load_module():
    spec = importlib.util.spec_from_file_location("build_trace_model", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


btm = _load_module()


def fake_manifest(*entries, version="test-1"):
    """Build a manifest dict from (slug, [workproduct slugs]) tuples."""
    files = [
        {"slug": slug, "type": "Domain", "related": {"workproducts": list(wps)}}
        for slug, wps in entries
    ]
    return {"version": version, "files": files}


class ProjectionTests(unittest.TestCase):
    def test_associations_project_slugs_onto_types(self):
        # The KB 'requirements' Domain co-lists vision + requirements + use-case.
        m = fake_manifest(
            ("requirements-1",
             ["glossary", "vision", "system-wide-requirements", "use-case"]),
        )
        assoc = btm.kb_associations(m)
        self.assertIn(frozenset(("vision", "requirement")), assoc)
        self.assertIn(frozenset(("requirement", "use-case")), assoc)
        self.assertIn(frozenset(("vision", "use-case")), assoc)

    def test_unknown_slugs_are_ignored(self):
        m = fake_manifest(("misc", ["glossary", "build", "design"]))
        # none of these map into the v1 spine -> no associations
        self.assertEqual(btm.kb_associations(m), set())


class CorroborationTests(unittest.TestCase):
    def test_kb_corroborated_flag_tracks_associations(self):
        # KB links vision<->requirement but says nothing about test products.
        m = fake_manifest(("requirements-1", ["vision", "system-wide-requirements"]))
        model = btm.build_model(m)
        edges = {(e["from"], e["to"]): e for e in model["trace_edges"]}
        self.assertTrue(edges[("requirement", "vision")]["kb_corroborated"])
        # test-case -> requirement edge exists but is not KB-corroborated here.
        self.assertFalse(edges[("test-case", "requirement")]["kb_corroborated"])

    def test_required_coverage_includes_requirement_verified_by_test_case(self):
        model = btm.build_model(fake_manifest())
        cov = {(r["type"], r["target"]) for r in model["coverage_rules"]}
        self.assertIn(("requirement", "test-case"), cov)


class SerializationTests(unittest.TestCase):
    def test_serialize_is_deterministic(self):
        m = fake_manifest(("requirements-1", ["vision", "use-case"]))
        a = btm.serialize(btm.build_model(m))
        b = btm.serialize(btm.build_model(m))
        self.assertEqual(a, b)
        self.assertTrue(a.endswith("\n"))
        json.loads(a)  # valid JSON


class IntegrationTests(unittest.TestCase):
    """Derive from the real vendored KB; assert the shipped contract."""

    @classmethod
    def setUpClass(cls):
        if not KB_MANIFEST.is_file():
            raise unittest.SkipTest("vendored KB manifest not present")
        cls.model = btm.build_model(btm.load_manifest(KB_MANIFEST))

    def test_requirement_to_test_case_is_a_coverage_edge(self):
        cov = {(r["type"], r["target"]) for r in self.model["coverage_rules"]}
        self.assertIn(("requirement", "test-case"), cov)

    def test_real_kb_corroborates_requirement_vision(self):
        edges = {(e["from"], e["to"]): e for e in self.model["trace_edges"]}
        self.assertTrue(edges[("requirement", "vision")]["kb_corroborated"])

    def test_committed_model_is_in_sync(self):
        # The committed scripts/trace-model.json must equal a fresh generation.
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, OK,
                         f"trace-model.json drifted:\n{proc.stderr}")

    def test_generation_is_idempotent(self):
        a = btm.serialize(self.model)
        b = btm.serialize(btm.build_model(btm.load_manifest(KB_MANIFEST)))
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
