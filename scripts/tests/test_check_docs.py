#!/usr/bin/env python3
"""Unit tests for scripts/check-docs.py (T-036).

Run with either:
    python3 -m unittest scripts.tests.test_check_docs
    python3 scripts/tests/test_check_docs.py

Hermetic: each test builds an isolated docs/ fixture in a tempdir and runs the
real validator against it (with the shipped schema + trace-model). The live repo
is never touched.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "check-docs.py"

OK, FAIL, USAGE = 0, 1, 2


def write_instance(docs, relpath, *, frontmatter, body=""):
    """Write a work-product instance. `frontmatter` is a list of YAML lines."""
    path = docs / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---", *frontmatter, "---", "", body]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run(docs, expect=None):
    cmd = [sys.executable, str(SCRIPT), "--docs", str(docs), "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if expect is not None:
        assert proc.returncode == expect, (
            f"expected exit {expect}, got {proc.returncode}\n"
            f"stdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def codes(proc):
    data = json.loads(proc.stdout)
    return data, {f["code"] for f in data["findings"]}


class _FixtureBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.docs = self.root / "docs"
        self.docs.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def vision(self, **kw):
        write_instance(self.docs, "product/vision.md", frontmatter=[
            "type: vision", "id: VIS-001", "title: Vision",
            "status: approved"], **kw)

    def make_test_case(self, iid="TC-031", **kw):
        write_instance(self.docs, f"tests/{iid}.md", frontmatter=[
            "type: test-case", f"id: {iid}", "title: Test",
            "status: implemented"], **kw)


class HappyPathTests(_FixtureBase):
    def test_fully_resolved_typed_set_passes(self):
        self.vision()
        self.make_test_case()
        write_instance(self.docs, "changes/REQ-014.md", frontmatter=[
            "type: requirement", "id: REQ-014", "title: Checkout",
            "status: approved", "traces-from: [VIS-001]",
            "verified-by: [TC-031]", "owner-role: analyst"])
        proc = run(self.docs, expect=OK)
        data, found = codes(proc)
        self.assertTrue(data["ok"])
        self.assertEqual(found, set())
        self.assertEqual(data["instances"], 3)

    def test_non_instance_files_are_skipped(self):
        # A template-provenance file is not an instance and must not be graded.
        write_instance(self.docs, "templates/vision.md", frontmatter=[
            "type: Template", "source_url: http://example/vision"])
        # An untyped narrative note, too.
        write_instance(self.docs, "notes/scratch.md", frontmatter=[
            "title: just notes"])
        proc = run(self.docs, expect=OK)
        data, _ = codes(proc)
        self.assertEqual(data["instances"], 0)
        self.assertTrue(data["ok"])


class SchemaTests(_FixtureBase):
    def test_missing_type_is_not_even_an_instance(self):
        # No `type` -> not discovered as an instance (skipped, not graded).
        write_instance(self.docs, "product/x.md", frontmatter=[
            "id: X-1", "status: approved"])
        proc = run(self.docs, expect=OK)
        data, _ = codes(proc)
        self.assertEqual(data["instances"], 0)

    def test_unknown_status_fails_schema(self):
        self.vision()  # ensure a valid baseline exists
        write_instance(self.docs, "changes/REQ-014.md", frontmatter=[
            "type: requirement", "id: REQ-014", "status: bogus",
            "traces-from: [VIS-001]"])
        proc = run(self.docs, expect=FAIL)
        _, found = codes(proc)
        self.assertIn("schema", found)

    def test_unknown_field_fails_schema(self):
        write_instance(self.docs, "product/vision.md", frontmatter=[
            "type: vision", "id: VIS-001", "status: approved",
            "traces_from: [VIS-000]"])  # underscore typo
        proc = run(self.docs, expect=FAIL)
        _, found = codes(proc)
        self.assertIn("schema", found)


class ReferenceTests(_FixtureBase):
    def test_dangling_verified_by_fails(self):
        self.vision()
        write_instance(self.docs, "changes/REQ-014.md", frontmatter=[
            "type: requirement", "id: REQ-014", "status: approved",
            "traces-from: [VIS-001]", "verified-by: [TC-999]"])
        proc = run(self.docs, expect=FAIL)
        _, found = codes(proc)
        self.assertIn("dangling-ref", found)

    def test_dangling_traces_from_fails(self):
        write_instance(self.docs, "changes/REQ-014.md", frontmatter=[
            "type: requirement", "id: REQ-014", "status: approved",
            "traces-from: [VIS-404]"])
        proc = run(self.docs, expect=FAIL)
        _, found = codes(proc)
        self.assertIn("dangling-ref", found)

    def test_verified_by_must_point_at_test_case(self):
        self.vision()
        # verified-by points at the vision, not a test-case.
        write_instance(self.docs, "changes/REQ-014.md", frontmatter=[
            "type: requirement", "id: REQ-014", "status: approved",
            "traces-from: [VIS-001]", "verified-by: [VIS-001]"])
        proc = run(self.docs, expect=FAIL)
        _, found = codes(proc)
        self.assertIn("bad-ref-type", found)

    def test_traces_from_invalid_upstream_type_fails(self):
        self.make_test_case()
        # A requirement cannot trace-from a test-case (not an allowed edge).
        write_instance(self.docs, "changes/REQ-014.md", frontmatter=[
            "type: requirement", "id: REQ-014", "status: approved",
            "traces-from: [TC-031]"])
        proc = run(self.docs, expect=FAIL)
        _, found = codes(proc)
        self.assertIn("bad-ref-type", found)

    def test_duplicate_id_fails(self):
        self.vision()
        write_instance(self.docs, "product/vision-copy.md", frontmatter=[
            "type: vision", "id: VIS-001", "status: draft"])
        proc = run(self.docs, expect=FAIL)
        _, found = codes(proc)
        self.assertIn("duplicate-id", found)


class DegradeModeTests(_FixtureBase):
    """When trace-model.json can't be loaded, the validator still runs schema +
    ref-existence checks; it just skips the upstream-type direction check
    instead of rejecting every traces-from ref."""

    def test_missing_model_still_runs_schema_and_ref_checks(self):
        self.vision()
        write_instance(self.docs, "changes/REQ-014.md", frontmatter=[
            "type: requirement", "id: REQ-014", "status: approved",
            "traces-from: [VIS-001]"])  # a *valid* edge; must not be flagged
        cmd = [sys.executable, str(SCRIPT),
               "--docs", str(self.docs),
               "--model", str(self.root / "no-such-model.json"),
               "--json"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, OK,
                         f"degrade mode should pass a valid set:\n{proc.stdout}")
        data, found = codes(proc)
        self.assertTrue(data["ok"])
        self.assertNotIn("bad-ref-type", found)

    def test_missing_model_still_catches_dangling_refs(self):
        write_instance(self.docs, "changes/REQ-014.md", frontmatter=[
            "type: requirement", "id: REQ-014", "status: approved",
            "traces-from: [VIS-404]"])  # dangling — model-independent
        cmd = [sys.executable, str(SCRIPT),
               "--docs", str(self.docs),
               "--model", str(self.root / "no-such-model.json"),
               "--json"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, FAIL)
        _, found = codes(proc)
        self.assertIn("dangling-ref", found)


class LinkTests(_FixtureBase):
    def test_broken_relative_md_link_fails(self):
        self.vision(body="See [the plan](./missing-plan.md) for details.")
        proc = run(self.docs, expect=FAIL)
        _, found = codes(proc)
        self.assertIn("broken-link", found)

    def test_resolvable_link_and_external_url_pass(self):
        self.make_test_case()  # tests/TC-031.md exists
        self.vision(body=(
            "Verified by [the test](../tests/TC-031.md). "
            "See [spec](https://example.com/spec.md) and [anchor](#section)."))
        proc = run(self.docs, expect=OK)
        data, _ = codes(proc)
        self.assertTrue(data["ok"])


# --------------------------------------------------------------------------
# T-037 — Coverage flag
# --------------------------------------------------------------------------
def run_coverage(docs, expect=None, model=None):
    cmd = [sys.executable, str(SCRIPT), "--docs", str(docs),
           "--coverage", "--json"]
    if model is not None:
        cmd += ["--model", str(model)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if expect is not None:
        assert proc.returncode == expect, (
            f"expected exit {expect}, got {proc.returncode}\n"
            f"stdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def write_model(root: Path, rules):
    """Write a minimal trace-model.json fixture with the given coverage rules."""
    model = {
        "schema": 1,
        "types": ["vision", "requirement", "work-item", "iteration-plan",
                  "use-case", "test-case", "decision"],
        "trace_edges": [
            {"from": "requirement", "to": "vision", "relation": "traces-from"},
            {"from": "work-item", "to": "requirement", "relation": "traces-from"},
            {"from": "test-case", "to": "requirement", "relation": "traces-from"},
        ],
        "coverage_rules": rules,
    }
    p = root / "trace-model.json"
    p.write_text(json.dumps(model), encoding="utf-8")
    return p


class CoverageTests(_FixtureBase):
    def test_off_by_default(self):
        """Without --coverage the validator does not emit coverage-gap findings,
        even when the project has uncovered requirements."""
        self.vision()
        write_instance(self.docs, "changes/REQ-014.md", frontmatter=[
            "type: requirement", "id: REQ-014", "status: approved",
            "traces-from: [VIS-001]"])  # no verified-by
        proc = run(self.docs, expect=OK)
        data, found = codes(proc)
        self.assertNotIn("coverage-gap", found)

    def test_approved_requirement_without_test_fails(self):
        self.vision()
        write_instance(self.docs, "changes/REQ-014.md", frontmatter=[
            "type: requirement", "id: REQ-014", "status: approved",
            "traces-from: [VIS-001]"])  # no verified-by
        proc = run_coverage(self.docs, expect=FAIL)
        data, found = codes(proc)
        self.assertIn("coverage-gap", found)
        # Severity tag is carried in the message.
        msgs = [f["message"] for f in data["findings"]
                if f["code"] == "coverage-gap"]
        self.assertTrue(any(m.startswith("[required]") for m in msgs))

    def test_draft_requirement_is_excluded_from_coverage(self):
        self.vision()
        write_instance(self.docs, "changes/REQ-099.md", frontmatter=[
            "type: requirement", "id: REQ-099", "status: draft",
            "traces-from: [VIS-001]"])  # draft -> not yet expected
        proc = run_coverage(self.docs, expect=OK)
        _, found = codes(proc)
        self.assertNotIn("coverage-gap", found)

    def test_obsolete_requirement_is_excluded_from_coverage(self):
        self.vision()
        write_instance(self.docs, "changes/REQ-O.md", frontmatter=[
            "type: requirement", "id: REQ-O", "status: obsolete"])
        proc = run_coverage(self.docs, expect=OK)
        _, found = codes(proc)
        self.assertNotIn("coverage-gap", found)

    def test_advisory_coverage_does_not_fail(self):
        """An advisory-severity gap is reported but does not change exit code."""
        self.vision()
        write_instance(self.docs, "changes/REQ-014.md", frontmatter=[
            "type: requirement", "id: REQ-014", "status: approved",
            "traces-from: [VIS-001]"])
        model = write_model(self.root, [
            {"type": "requirement", "relation": "verified-by",
             "target": "test-case", "severity": "advisory"},
        ])
        proc = run_coverage(self.docs, expect=OK, model=model)
        data, found = codes(proc)
        # The gap is still surfaced…
        self.assertIn("coverage-gap", found)
        # …but the run is OK.
        self.assertTrue(data["ok"])

    def test_covered_requirement_passes_coverage(self):
        self.vision()
        self.make_test_case()
        write_instance(self.docs, "changes/REQ-014.md", frontmatter=[
            "type: requirement", "id: REQ-014", "status: approved",
            "traces-from: [VIS-001]", "verified-by: [TC-031]"])
        proc = run_coverage(self.docs, expect=OK)
        _, found = codes(proc)
        self.assertNotIn("coverage-gap", found)

    def test_work_item_without_requirement_fails_coverage(self):
        write_instance(self.docs, "iter/WI-001.md", frontmatter=[
            "type: work-item", "id: WI-001", "status: approved"])
        proc = run_coverage(self.docs, expect=FAIL)
        _, found = codes(proc)
        self.assertIn("coverage-gap", found)


class ChangeFolderRefTests(_FixtureBase):
    """T-090: a change folder is the system's work-item instance, so a
    work-product may traces-from a change-folder id even though its plan.md is a
    task-spec (no typed frontmatter)."""

    def _lane(self, lane_id):
        # A plain task-spec (status ready) — NOT a typed maturity instance.
        d = self.docs / "changes" / lane_id
        d.mkdir(parents=True, exist_ok=True)
        (d / "plan.md").write_text(
            "---\nid: %s\nstatus: ready\npriority: high\n---\n# %s\n"
            "## Operations\n- [ ] do it\n" % (lane_id, lane_id), encoding="utf-8")

    def _iteration_plan(self, traces):
        write_instance(self.docs, "phases/inception/iteration-I1-plan.md",
                       frontmatter=[
                           "type: iteration-plan", "id: IP-I1",
                           "title: Iteration I1", "status: approved",
                           "traces-from: [%s]" % ", ".join(traces),
                           "owner-role: project-manager", "iteration: inception-1"],
                       body="## Evaluation Criteria\n- done")

    def test_iteration_plan_tracing_change_folder_resolves(self):
        self._lane("I1-001")
        self._lane("I1-002")
        self._iteration_plan(["I1-001", "I1-002"])
        proc = run(self.docs, expect=OK)
        data, found = codes(proc)
        self.assertTrue(data["ok"])
        self.assertNotIn("dangling-ref", found)

    def test_ref_to_missing_change_folder_still_dangles(self):
        self._iteration_plan(["I1-999"])  # no such change folder
        proc = run(self.docs, expect=FAIL)
        _, found = codes(proc)
        self.assertIn("dangling-ref", found)


class ArchetypeDefaultsCLITests(unittest.TestCase):
    """T-115: --show-archetype-defaults answers "what applies when
    docs/project-config.yaml is absent" in one call, no docs/ tree needed."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location("check_docs", SCRIPT)
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def _run(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--show-archetype-defaults"],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, OK, proc.stderr)
        return json.loads(proc.stdout)

    def test_exits_ok_with_no_docs_dir(self):
        # No --docs given, and no docs/ dir exists in cwd — must not try to
        # load or validate anything.
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--show-archetype-defaults"],
            capture_output=True, text=True, cwd=tempfile.gettempdir())
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_default_when_absent_names_both_axes(self):
        data = self._run()
        msg = data["default_when_absent"]
        self.assertIn("No archetype tailoring", msg)
        self.assertIn("tracks.md", msg)

    def test_archetypes_match_the_real_dict(self):
        data = self._run()
        self.assertEqual(
            set(data["archetypes"].keys()),
            set(self.mod.PROCESS_ARCHETYPE_DEFAULTS.keys()))
        for name, expected in self.mod.PROCESS_ARCHETYPE_DEFAULTS.items():
            self.assertEqual(data["archetypes"][name], expected)


if __name__ == "__main__":
    unittest.main()
