#!/usr/bin/env python3
"""Unit tests for the project-side check-docs commit hook (T-039).

Run with either:
    python3 -m unittest scripts.tests.test_check_docs_hook
    python3 scripts/tests/test_check_docs_hook.py

Hermetic: each test stages a tempdir with a copy of the validator + hook,
crafts a ``PreToolUse`` payload, and runs the hook the same way Claude
Code would. The live repo is never touched.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO / "scripts"
HOOK = REPO / "docs-eng-process" / ".claude-templates" / "scripts" / "hooks" / "check-docs.py"
VALIDATOR = SCRIPTS_DIR / "check-docs.py"
SCHEMA = SCRIPTS_DIR / "docs-meta.schema.json"
MODEL = SCRIPTS_DIR / "trace-model.json"
CLAIMS = SCRIPTS_DIR / "openup-claims.py"


def _payload(command, *, tool="Bash"):
    return json.dumps({
        "tool_name": tool,
        "tool_input": {"command": command},
    })


def _run_hook(stdin_json, cwd):
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin_json, text=True,
        capture_output=True, cwd=str(cwd),
        timeout=20,
    )
    return proc


class _FixtureBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "scripts").mkdir()
        # Ship the validator + its peers so the hook's subprocess call
        # against ``scripts/check-docs.py`` succeeds.
        for src in (VALIDATOR, SCHEMA, MODEL, CLAIMS):
            shutil.copy(src, self.root / "scripts" / src.name)
        # A repo for git rev-parse to find.
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=False)
        self.docs = self.root / "docs"
        self.docs.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def write_instance(self, relpath, *, frontmatter, body=""):
        path = self.docs / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["---", *frontmatter, "---", "", body]
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def write_config(self, body: str):
        (self.docs / "project-config.yaml").write_text(body,
                                                      encoding="utf-8")


class PassThroughTests(_FixtureBase):
    """Non-git or non-Bash payloads must always exit 0 (allow)."""

    def test_non_bash_tool_passes(self):
        proc = _run_hook(_payload("git commit", tool="Edit"), self.root)
        self.assertEqual(proc.returncode, 0)

    def test_non_commit_bash_passes(self):
        proc = _run_hook(_payload("git status"), self.root)
        self.assertEqual(proc.returncode, 0)

    def test_substring_commit_does_not_trigger(self):
        """An unrelated ``commit`` substring (e.g. in a message) must not match."""
        proc = _run_hook(_payload("echo 'commit me'"), self.root)
        self.assertEqual(proc.returncode, 0)

    def test_missing_validator_is_fail_open(self):
        (self.root / "scripts" / "check-docs.py").unlink()
        proc = _run_hook(_payload("git commit -m foo"), self.root)
        self.assertEqual(proc.returncode, 0)


class CommitBlockingTests(_FixtureBase):
    def test_clean_docs_passes_git_commit(self):
        self.write_instance("vision.md", frontmatter=[
            "type: vision", "id: VIS-001", "title: V",
            "status: approved"])
        proc = _run_hook(_payload("git commit -m x"), self.root)
        self.assertEqual(proc.returncode, 0)

    def test_schema_error_blocks_commit(self):
        self.write_instance("vision.md", frontmatter=[
            "type: vision", "id: VIS-001", "title: V",
            "status: bogus"])  # invalid status
        proc = _run_hook(_payload("git commit -m x"), self.root)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("Blocked", proc.stderr)

    def test_coverage_gap_blocks_by_default(self):
        self.write_instance("vision.md", frontmatter=[
            "type: vision", "id: VIS-001", "status: approved"])
        self.write_instance("changes/REQ-014.md", frontmatter=[
            "type: requirement", "id: REQ-014", "status: approved",
            "traces-from: [VIS-001]"])  # no verified-by -> required gap
        proc = _run_hook(_payload("git commit -m x"), self.root)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("coverage-gap", proc.stderr)


class TailoringTests(_FixtureBase):
    """trace_rules: in docs/project-config.yaml tunes hook strictness."""

    def setUp(self):
        super().setUp()
        # A typical scenario: an approved requirement missing its test.
        self.write_instance("vision.md", frontmatter=[
            "type: vision", "id: VIS-001", "status: approved"])
        self.write_instance("changes/REQ-014.md", frontmatter=[
            "type: requirement", "id: REQ-014", "status: approved",
            "traces-from: [VIS-001]"])

    def test_disabled_skips_hook(self):
        self.write_config("trace_rules:\n  enabled: false\n")
        proc = _run_hook(_payload("git commit -m x"), self.root)
        self.assertEqual(proc.returncode, 0)

    def test_coverage_off_drops_the_coverage_pass(self):
        self.write_config("trace_rules:\n  coverage: false\n")
        # Schema/refs still run — but our fixture is schema-clean, so:
        proc = _run_hook(_payload("git commit -m x"), self.root)
        self.assertEqual(proc.returncode, 0)

    def test_severity_downgrade_lets_advisory_gap_pass(self):
        self.write_config(
            'trace_rules:\n'
            '  severity:\n'
            '    "requirement -> verified-by -> test-case": advisory\n'
        )
        proc = _run_hook(_payload("git commit -m x"), self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # The gap is still surfaced for the model to see.
        self.assertIn("REQ-014", proc.stderr + proc.stdout)


class YamlParserTests(unittest.TestCase):
    """The tiny stdlib YAML reader needs to be correct enough for the
    keys this hook reads. Exercise it directly."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location("check_docs_hook", HOOK)
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def test_top_level_scalars(self):
        cfg = self.mod.parse_simple_yaml(
            "trace_rules:\n  enabled: false\n  coverage: true\n")
        self.assertEqual(cfg["trace_rules"]["enabled"], False)
        self.assertEqual(cfg["trace_rules"]["coverage"], True)

    def test_nested_severity_map(self):
        cfg = self.mod.parse_simple_yaml(
            'trace_rules:\n'
            '  severity:\n'
            '    "requirement -> verified-by -> test-case": advisory\n'
        )
        sev = cfg["trace_rules"]["severity"]
        self.assertEqual(sev["requirement -> verified-by -> test-case"],
                         "advisory")

    def test_comments_and_blank_lines_skipped(self):
        cfg = self.mod.parse_simple_yaml(
            "# leading comment\n\ntrace_rules:\n  enabled: true\n")
        self.assertEqual(cfg["trace_rules"]["enabled"], True)


if __name__ == "__main__":
    unittest.main()
