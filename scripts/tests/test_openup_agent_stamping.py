#!/usr/bin/env python3
"""Hermetic tests for engine-owned frontmatter stamping (T-104).

Run with either:
    python3 -m unittest scripts.tests.test_openup_agent_stamping
    python3 scripts/tests/test_openup_agent_stamping.py

Everything runs against a temp docs/ tree — zero network, zero LLM. The one
integration case runs the real ``check-docs.py`` (subprocess) on a stamped
artifact: the gate is the critic, so the gate is what the test consults.
"""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from openup_agent import stamping  # noqa: E402


def _load_claims():
    spec = importlib.util.spec_from_file_location(
        "claims", SCRIPTS / "openup-claims.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class StampFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="stamping-")
        self.root = Path(self.tmp.name)
        self.docs = self.root / "docs" / "product"
        self.docs.mkdir(parents=True)
        self.addCleanup(self.tmp.cleanup)

    def _write(self, name, text):
        path = self.docs / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_stamps_body_only_artifact(self):
        path = self._write("vision.md", "# Product Vision: Alpha\n\nBody.\n")
        result = stamping.stamp_file(self.root, path, "vision")
        self.assertEqual(result["id"], "VIS-001")
        self.assertEqual(result["status"], "draft")
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\ntype: vision\nid: VIS-001\n"))
        self.assertIn('title: "Product Vision: Alpha"', text)
        self.assertIn("status: draft", text)
        self.assertIn("# Product Vision: Alpha\n\nBody.\n", text)

    def test_replaces_model_written_frontmatter(self):
        path = self._write("uc.md", (
            '---\ntype: use-case\nid: BOGUS-9\ntitle: "Model Title"\n'
            'status: verified\n---\n\nNo heading body.\n'))
        result = stamping.stamp_file(self.root, path, "use-case")
        text = path.read_text(encoding="utf-8")
        self.assertEqual(result["id"], "UC-001")
        self.assertNotIn("BOGUS", text)
        self.assertNotIn("verified", text)
        self.assertEqual(text.count("---"), 2)  # one fence pair, no duplicate
        # no heading in the body -> the model's own title is salvaged
        self.assertEqual(result["title"], "Model Title")
        self.assertIn("No heading body.\n", text)

    def test_second_instance_allocates_next_id(self):
        a = self._write("vision.md", "# First\n\nBody.\n")
        b = self._write("vision-2.md", "# Second\n\nBody.\n")
        self.assertEqual(stamping.stamp_file(self.root, a, "vision")["id"],
                         "VIS-001")
        self.assertEqual(stamping.stamp_file(self.root, b, "vision")["id"],
                         "VIS-002")

    def test_id_referenced_anywhere_is_taken(self):
        # An id woven into another doc's trace web (or prose) is not reissued.
        self._write("notes.md", "Supersedes VIS-005 per review.\n")
        path = self._write("vision.md", "# V\n\nBody.\n")
        self.assertEqual(stamping.stamp_file(self.root, path, "vision")["id"],
                         "VIS-006")

    def test_restamp_keeps_existing_valid_id(self):
        # Re-running normalize on an already-stamped artifact must not
        # reallocate — other instances may reference the id in trace fields.
        path = self._write("vision.md", "# V\n\nBody.\n")
        first = stamping.stamp_file(self.root, path, "vision")
        again = stamping.stamp_file(self.root, path, "vision")
        self.assertEqual(first["id"], "VIS-001")
        self.assertEqual(again["id"], "VIS-001")

    def test_unknown_type_raises(self):
        path = self._write("poem.md", "# Ode\n\nBody.\n")
        with self.assertRaises(ValueError):
            stamping.stamp_file(self.root, path, "poem")

    def test_unterminated_fence_is_body_not_eaten(self):
        path = self._write("broken.md", "---\ntype: vision\nno closing fence\n")
        stamping.stamp_file(self.root, path, "vision")
        text = path.read_text(encoding="utf-8")
        # the malformed original text survives after the stamped block
        self.assertIn("no closing fence", text)

    def test_title_quotes_sanitized(self):
        path = self._write("q.md", '# He said "go"\n\nBody.\n')
        result = stamping.stamp_file(self.root, path, "vision")
        self.assertEqual(result["title"], 'He said "go"')
        self.assertIn("title: \"He said 'go'\"", path.read_text(encoding="utf-8"))

    def test_shared_parser_reads_stamped_block(self):
        path = self._write("vision.md", "# Product Vision: Alpha\n\nBody.\n")
        stamping.stamp_file(self.root, path, "vision")
        fm = _load_claims().parse_frontmatter(path)
        self.assertEqual(fm, {"type": "vision", "id": "VIS-001",
                              "title": "Product Vision: Alpha",
                              "status": "draft"})

    def test_check_docs_accepts_stamped_artifact(self):
        path = self._write("vision.md", "# Product Vision: Alpha\n\nBody.\n")
        stamping.stamp_file(self.root, path, "vision")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "check-docs.py"),
             "--docs", str(self.root / "docs")],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
