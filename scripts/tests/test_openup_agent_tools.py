#!/usr/bin/env python3
"""Unit tests for the reference-driver six-tool surface (T-072).

Run with either:
    python3 -m unittest scripts.tests.test_openup_agent_tools
    python3 scripts/tests/test_openup_agent_tools.py

Hermetic: each test builds an isolated tmp working root; no network, no repo
dependency. Exercises tools.Tools exactly as loop._dispatch_tool_calls would.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openup_agent import tools  # noqa: E402


class ToolsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.t = tools.Tools(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, rel, content):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    # -- read_file --------------------------------------------------------
    def test_read_file_full(self):
        self._write("a.txt", "hello\nworld\n")
        self.assertEqual(self.t.read_file("a.txt"), "hello\nworld\n")

    def test_read_file_offset_limit(self):
        self._write("a.txt", "l0\nl1\nl2\nl3\n")
        self.assertEqual(self.t.read_file("a.txt", offset=1, limit=2), "l1\nl2")

    def test_read_file_missing(self):
        self.assertTrue(self.t.read_file("nope.txt").startswith("ERROR: no such file"))

    def test_read_file_directory(self):
        (self.root / "sub").mkdir()
        self.assertIn("is a directory", self.t.read_file("sub"))

    def test_read_file_traversal_refused(self):
        self.assertIn("escapes the working root", self.t.read_file("../secret"))

    # -- write_file -------------------------------------------------------
    def test_write_file_creates_parents(self):
        msg = self.t.write_file("deep/nested/f.txt", "x")
        self.assertIn("wrote", msg)
        self.assertEqual((self.root / "deep/nested/f.txt").read_text(), "x")

    def test_write_file_traversal_refused(self):
        self.assertIn("escapes the working root", self.t.write_file("../evil", "x"))

    # -- edit_file --------------------------------------------------------
    def test_edit_file_unique(self):
        self._write("p.md", "- [ ] step one\n- [ ] step two\n")
        msg = self.t.edit_file("p.md", "- [ ] step one", "- [x] step one")
        self.assertIn("1 replacement", msg)
        self.assertIn("- [x] step one", (self.root / "p.md").read_text())

    def test_edit_file_absent_old_str(self):
        self._write("p.md", "content\n")
        self.assertIn("not found", self.t.edit_file("p.md", "ZZZ", "y"))

    def test_edit_file_non_unique(self):
        self._write("p.md", "dup\ndup\n")
        out = self.t.edit_file("p.md", "dup", "x")
        self.assertIn("not unique", out)
        # file unchanged after a non-unique edit
        self.assertEqual((self.root / "p.md").read_text(), "dup\ndup\n")

    def test_edit_file_missing(self):
        self.assertIn("no such file", self.t.edit_file("nope", "a", "b"))

    # -- glob -------------------------------------------------------------
    def test_glob_matches(self):
        self._write("docs/changes/T-1/plan.md", "")
        self._write("docs/changes/T-2/plan.md", "")
        out = self.t.glob("docs/changes/*/plan.md")
        self.assertIn("docs/changes/T-1/plan.md", out)
        self.assertIn("docs/changes/T-2/plan.md", out)

    def test_glob_no_matches(self):
        self.assertIn("no matches", self.t.glob("nothing/*.zzz"))

    # -- grep -------------------------------------------------------------
    def test_grep_finds_line(self):
        self._write("r.md", "alpha\nid: T-072\nbeta\n")
        out = self.t.grep(r"T-\d+", "r.md")
        self.assertIn("r.md:2:id: T-072", out)

    def test_grep_no_match(self):
        self._write("r.md", "nothing here\n")
        self.assertEqual(self.t.grep("ZZZ", "r.md"), "(no matches)")

    def test_grep_invalid_regex(self):
        self.assertIn("invalid regex", self.t.grep("(", "."))

    # -- exec allowlist ---------------------------------------------------
    def test_exec_refuses_non_allowlisted(self):
        out = self.t.exec("rm -rf /")
        self.assertTrue(out.startswith("REFUSED"))
        self.assertIn("allowlist", out)

    def test_exec_refuses_arbitrary_python(self):
        # python3 is only allowed against scripts/*.py
        self.assertTrue(self.t.exec("python3 -c \"print(1)\"").startswith("REFUSED"))

    def test_exec_refuses_empty(self):
        self.assertIn("empty command", self.t.exec("   "))

    def test_exec_allows_git(self):
        out = self.t.exec("git --version")
        self.assertIn("exit=0", out)
        self.assertIn("git version", out)

    def test_exec_allows_scripts_python(self):
        self._write("scripts/hi.py", "print('hi from script')\n")
        out = self.t.exec("python3 scripts/hi.py")
        self.assertIn("exit=0", out)
        self.assertIn("hi from script", out)

    # -- dispatch ---------------------------------------------------------
    def test_dispatch_unknown_tool(self):
        self.assertIn("unknown tool", self.t.dispatch("frobnicate", {}))

    def test_dispatch_bad_arguments(self):
        self.assertIn("bad arguments", self.t.dispatch("read_file", {"wrong": 1}))

    def test_tool_defs_cover_named_surface(self):
        names = {d["function"]["name"] for d in tools.TOOL_DEFS}
        self.assertEqual(names, set(tools.TOOL_NAMES))
        self.assertEqual(len(tools.TOOL_DEFS), 6)


if __name__ == "__main__":
    unittest.main()
