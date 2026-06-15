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


if __name__ == "__main__":
    unittest.main()
