#!/usr/bin/env python3
"""Unit tests for the Development Case `process:` section (T-076).

Run with either:
    python3 -m unittest scripts.tests.test_process_config
    python3 scripts/tests/test_process_config.py

Hermetic: parser/resolver/validator are exercised in-process; the check-docs.py
gate is run as a subprocess against an isolated docs/ fixture. The live repo is
never touched.
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
CHECK_DOCS = SCRIPTS_DIR / "check-docs.py"
DOCTOR = SCRIPTS_DIR / "openup-doctor.py"

OK, FAIL = 0, 1


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cd = _load(CHECK_DOCS, "_t076_check_docs")
doctor = _load(DOCTOR, "_t076_doctor")


def run_check_docs(docs: Path):
    cmd = [sys.executable, str(CHECK_DOCS), "--docs", str(docs), "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(proc.stdout)
    return proc.returncode, data


def write_config(docs: Path, text: str):
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "project-config.yaml").write_text(text, encoding="utf-8")


# ── R1: archetype default resolution + explicit override ─────────────────────
class ResolveDefaults(unittest.TestCase):
    def test_override_wins_over_archetype_default(self):
        # mvp construction default: {iterations: many, parallel: False}.
        # An explicit parallel:true override must win.
        proc = {"archetype": "mvp",
                "phases": {"construction": {"parallel": True}}}
        resolved = cd.resolve_process(proc)
        self.assertTrue(resolved["phases"]["construction"]["parallel"])
        # Unmentioned iterations key keeps the mvp default.
        self.assertEqual(resolved["phases"]["construction"]["iterations"], "many")

    def test_unmentioned_phase_keeps_archetype_default(self):
        resolved = cd.resolve_process({"archetype": "mvp",
                                       "phases": {"construction": {"parallel": True}}})
        # transition was never mentioned -> mvp default gate:human survives.
        self.assertEqual(resolved["phases"]["transition"], {"gate": "human"})

    def test_milestone_review_override(self):
        resolved = cd.resolve_process({"archetype": "product",
                                       "milestone_review": "auto-assess"})
        self.assertEqual(resolved["milestone_review"], "auto-assess")


# ── R2: quick degenerates to today's quick-task ceremony ─────────────────────
class QuickDegeneration(unittest.TestCase):
    def test_quick_defaults(self):
        r = cd.resolve_process({"archetype": "quick"})
        self.assertEqual(r["phases"]["elaboration"]["iterations"], "skip")
        self.assertEqual(r["phases"]["construction"]["iterations"], 1)
        self.assertFalse(r["phases"]["construction"]["parallel"])
        self.assertEqual(r["milestone_review"], "auto-assess")


# ── Parser shapes ────────────────────────────────────────────────────────────
class ParserShapes(unittest.TestCase):
    def test_absent_section_is_none(self):
        self.assertIsNone(cd.parse_process_section("context: hi\nrules: {}\n"))

    def test_inline_flow_map(self):
        text = ("process:\n"
                "  archetype: mvp\n"
                "  phases:\n"
                "    inception: { iterations: 1, artifacts: [vision, risk-list] }\n"
                "  milestone_review: human\n")
        p = cd.parse_process_section(text)
        self.assertEqual(p["archetype"], "mvp")
        self.assertEqual(p["phases"]["inception"]["artifacts"], ["vision", "risk-list"])
        self.assertEqual(p["milestone_review"], "human")

    def test_block_map(self):
        text = ("process:\n"
                "  archetype: product\n"
                "  phases:\n"
                "    elaboration:\n"
                "      iterations: auto\n"
                "      parallel: true\n")
        p = cd.parse_process_section(text)
        self.assertEqual(p["phases"]["elaboration"]["iterations"], "auto")
        self.assertTrue(p["phases"]["elaboration"]["parallel"])

    def test_trailing_comment_stripped(self):
        p = cd.parse_process_section("process:\n  archetype: quick   # a comment\n")
        self.assertEqual(p["archetype"], "quick")


# ── R3: check-docs.py gate (structural validation, blocking) ─────────────────
class CheckDocsGate(unittest.TestCase):
    def _run(self, config_text):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            write_config(docs, config_text)
            return run_check_docs(docs)

    def test_absent_section_passes(self):
        code, data = self._run("context: hi\nrules: {}\n")
        self.assertEqual(code, OK)
        self.assertNotIn("process-config", {f["code"] for f in data["findings"]})

    def test_valid_section_passes(self):
        code, data = self._run("process:\n  archetype: product\n")
        self.assertEqual(code, OK)

    def test_unknown_archetype_blocks(self):
        code, data = self._run("process:\n  archetype: enterprise\n")
        self.assertEqual(code, FAIL)
        msgs = [f["message"] for f in data["findings"] if f["code"] == "process-config"]
        self.assertTrue(any("archetype" in m for m in msgs), msgs)

    def test_unknown_phase_blocks(self):
        code, data = self._run("process:\n  archetype: mvp\n  phases:\n"
                               "    testing: { iterations: 1 }\n")
        self.assertEqual(code, FAIL)

    def test_bad_iterations_value_blocks(self):
        code, data = self._run("process:\n  archetype: mvp\n  phases:\n"
                               "    inception: { iterations: lots }\n")
        self.assertEqual(code, FAIL)

    def test_missing_archetype_blocks(self):
        code, data = self._run("process:\n  milestone_review: human\n")
        self.assertEqual(code, FAIL)

    def test_safeguard_waiving_key_blocks(self):
        code, data = self._run("process:\n  archetype: mvp\n  waive: safeguard\n")
        self.assertEqual(code, FAIL)
        msgs = [f["message"] for f in data["findings"] if f["code"] == "process-config"]
        self.assertTrue(any("waive" in m for m in msgs), msgs)


# ── R4: openup-doctor read-only process-config check ─────────────────────────
class DoctorProcessConfig(unittest.TestCase):
    def _repo(self, tmp, config_text=None):
        root = Path(tmp)
        (root / "scripts").mkdir(parents=True, exist_ok=True)
        # doctor imports the project's own check-docs.py + openup-claims.py.
        for name in ("check-docs.py", "openup-claims.py"):
            (root / "scripts" / name).write_text((SCRIPTS_DIR / name).read_text())
        (root / "docs").mkdir(parents=True, exist_ok=True)
        if config_text is not None:
            (root / "docs" / "project-config.yaml").write_text(config_text)
        return str(root)

    def _sev(self, findings):
        return [(f.severity, f.message) for f in findings]

    def test_valid_is_info(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp, "process:\n  archetype: mvp\n")
            out = doctor.check_process_config(repo)
            self.assertEqual([s for s, _ in self._sev(out)], ["info"])
            self.assertIn("archetype=mvp", out[0].message)

    def test_invalid_is_warning_never_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp, "process:\n  archetype: bogus\n")
            out = doctor.check_process_config(repo)
            sevs = [s for s, _ in self._sev(out)]
            self.assertIn("warning", sevs)
            self.assertNotIn("error", sevs)
            self.assertIn("check-docs.py", out[0].message)

    def test_absent_section_is_info(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp, "context: hi\n")
            out = doctor.check_process_config(repo)
            self.assertEqual([s for s, _ in self._sev(out)], ["info"])

    def test_no_config_is_info(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp, None)
            out = doctor.check_process_config(repo)
            self.assertEqual([s for s, _ in self._sev(out)], ["info"])


if __name__ == "__main__":
    unittest.main()
