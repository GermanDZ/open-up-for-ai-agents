#!/usr/bin/env python3
"""Unit tests for scripts/openup-doctor.py (T-053).

Run with either:
    python3 -m unittest scripts.tests.test_openup_doctor
    python3 scripts/tests/test_openup_doctor.py

Hermetic: each test builds an isolated project tree in a tempdir (its own
docs-eng-process/.template-version, scripts/, .openup/) and runs the real
diagnostic against it with --repo-root. The live repo is never touched and no
network/baseline is required unless a test creates one.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "openup-doctor.py"
REAL_STATE = SCRIPTS_DIR / "openup-state.py"
REAL_STATE_SCHEMA = SCRIPTS_DIR / "openup-state.schema.json"

OK, ERROR_EXIT, USAGE_EXIT = 0, 1, 2

STUB_PASS = "#!/usr/bin/env python3\nimport sys; sys.exit(0)\n"
STUB_FAIL = "#!/usr/bin/env python3\nimport sys; print('boom'); sys.exit(1)\n"


def make_project(tmp, *, version="1.5.0", scripts=None, state=None):
    """Build a minimal project tree. `scripts` maps filename->contents."""
    root = Path(tmp)
    (root / "docs-eng-process").mkdir(parents=True, exist_ok=True)
    if version is not None:
        (root / "docs-eng-process" / ".template-version").write_text(version + "\n")
    sdir = root / "scripts"
    sdir.mkdir(parents=True, exist_ok=True)
    for name, contents in (scripts or {}).items():
        (sdir / name).write_text(contents)
    if state is not None:
        odir = root / ".openup"
        odir.mkdir(parents=True, exist_ok=True)
        (odir / "state.json").write_text(state)
        # state-integrity reuses the real validator — copy it in.
        shutil.copy(REAL_STATE, sdir / "openup-state.py")
        shutil.copy(REAL_STATE_SCHEMA, sdir / "openup-state.schema.json")
    return root


def run_doctor(root, *extra):
    p = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(root), *extra],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    return p.returncode, p.stdout, p.stderr


def run_doctor_json(root, *extra):
    code, out, err = run_doctor(root, "--json", *extra)
    return code, json.loads(out), err


def findings_by_check(payload, check):
    return [f for f in payload["findings"] if f["check"] == check]


class FrameworkDriftTests(unittest.TestCase):
    def test_offline_reports_version_and_does_not_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp, version="1.5.0")
            code, payload, _ = run_doctor_json(root)
            drift = findings_by_check(payload, "framework-drift")
            msgs = " ".join(f["message"] for f in drift)
            self.assertIn("1.5.0", msgs)
            self.assertIn("scripts not verified", msgs)
            self.assertTrue(all(f["severity"] != "error" for f in drift))
            self.assertEqual(code, OK)

    def test_behind_version_is_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            with tempfile.TemporaryDirectory() as base_tmp:
                root = make_project(tmp, version="1.4.0")
                base = make_project(base_tmp, version="1.5.0",
                                    scripts={"process-manifest.txt": ""})
                code, payload, _ = run_doctor_json(root, "--framework-path", str(base))
                warns = [f for f in findings_by_check(payload, "framework-drift")
                         if f["severity"] == "warning"]
                self.assertTrue(any("behind on framework version" in f["message"]
                                    for f in warns))

    def test_missing_cli_is_error_and_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            with tempfile.TemporaryDirectory() as base_tmp:
                root = make_project(tmp, version="1.5.0")
                base = make_project(
                    base_tmp, version="1.5.0",
                    scripts={"process-manifest.txt": "a.py\n", "a.py": STUB_PASS})
                # root has no scripts/a.py -> missing shipped CLI
                code, payload, _ = run_doctor_json(root, "--framework-path", str(base))
                errs = [f for f in payload["findings"] if f["severity"] == "error"]
                self.assertTrue(any("missing shipped CLI: scripts/a.py" in f["message"]
                                    for f in errs))
                self.assertEqual(code, ERROR_EXIT)
                self.assertFalse(payload["ok"])

    def test_modified_cli_is_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            with tempfile.TemporaryDirectory() as base_tmp:
                base = make_project(
                    base_tmp, version="1.5.0",
                    scripts={"process-manifest.txt": "a.py\n", "a.py": STUB_PASS})
                root = make_project(tmp, version="1.5.0",
                                    scripts={"a.py": STUB_FAIL})  # different bytes
                code, payload, _ = run_doctor_json(root, "--framework-path", str(base))
                warns = [f for f in payload["findings"] if f["severity"] == "warning"]
                self.assertTrue(any("locally modified: scripts/a.py" in f["message"]
                                    for f in warns))


class StateIntegrityTests(unittest.TestCase):
    def test_absent_state_is_info(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp)
            code, payload, _ = run_doctor_json(root)
            st = findings_by_check(payload, "state-integrity")
            self.assertEqual(len(st), 1)
            self.assertEqual(st[0]["severity"], "info")
            self.assertEqual(code, OK)

    def test_corrupt_state_is_error_and_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp, state="{ not valid json")
            code, payload, _ = run_doctor_json(root)
            st = findings_by_check(payload, "state-integrity")
            self.assertEqual(st[0]["severity"], "error")
            self.assertIn("invalid", st[0]["message"])
            self.assertEqual(code, ERROR_EXIT)

    def test_valid_state_is_info(self):
        valid = json.dumps({
            "schema": 1, "task_id": "T-001", "iteration": 1, "phase": "construction",
            "track": "standard", "branch": "feat/x", "worktree": "/tmp/x",
            "session_id": "s1", "started_at": "2026-01-01T00:00:00Z",
            "gates": {"team_deployed": False, "plan_persisted": True,
                      "log_written": False, "roadmap_synced": False,
                      "retro_due": False},
            "iterations_since_retro": 0,
        })
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp, state=valid)
            code, payload, _ = run_doctor_json(root)
            st = findings_by_check(payload, "state-integrity")
            self.assertEqual(st[0]["severity"], "info")
            self.assertIn("valid", st[0]["message"])


class AggregationTests(unittest.TestCase):
    def test_absent_tool_is_info_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp)  # no aggregated tools present
            code, payload, _ = run_doctor_json(root)
            agg = findings_by_check(payload, "aggregate")
            self.assertTrue(agg)
            self.assertTrue(all(f["severity"] == "info" for f in agg))
            self.assertTrue(any("not present" in f["message"] for f in agg))
            self.assertEqual(code, OK)

    def test_failing_check_docs_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp, scripts={"check-docs.py": STUB_FAIL})
            code, payload, _ = run_doctor_json(root)
            agg = findings_by_check(payload, "aggregate")
            self.assertTrue(any(f["severity"] == "error"
                                and "check-docs.py" in f["message"] for f in agg))
            self.assertEqual(code, ERROR_EXIT)

    def test_failing_derived_view_is_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp, scripts={"docs-index.py": STUB_FAIL})
            code, payload, _ = run_doctor_json(root)
            agg = findings_by_check(payload, "aggregate")
            self.assertTrue(any(f["severity"] == "warning"
                                and "docs-index.py" in f["message"] for f in agg))
            self.assertEqual(code, OK)


class ContractTests(unittest.TestCase):
    def test_json_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp)
            code, payload, _ = run_doctor_json(root)
            self.assertIn("ok", payload)
            self.assertIn("findings", payload)
            for f in payload["findings"]:
                # Base contract keys must be present; T-117 added optional
                # fix_class/fix_cmd, so assert a superset rather than exact set.
                self.assertLessEqual({"severity", "check", "message"}, set(f))
                self.assertIn(f["severity"], {"error", "warning", "info"})

    def test_unresolvable_root_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "does-not-exist")
            code, _out, _err = run_doctor(missing)
            self.assertEqual(code, USAGE_EXIT)

    def test_read_only_does_not_mutate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp, scripts={"check-docs.py": STUB_FAIL})
            before = {p: p.stat().st_mtime_ns for p in Path(root).rglob("*")
                      if p.is_file()}
            run_doctor(root)
            after = {p: p.stat().st_mtime_ns for p in Path(root).rglob("*")
                     if p.is_file()}
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
