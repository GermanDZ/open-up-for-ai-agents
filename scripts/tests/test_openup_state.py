#!/usr/bin/env python3
"""Unit tests for scripts/openup-state.py.

Run with either:
    python3 -m unittest scripts.tests.test_openup_state
    python3 scripts/tests/test_openup_state.py
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "openup-state.py"


def run(args, state_dir, expect_code=None):
    """Invoke the CLI with --state-dir injected; return CompletedProcess."""
    cmd = [sys.executable, str(SCRIPT)] + args + ["--state-dir", str(state_dir)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if expect_code is not None:
        assert proc.returncode == expect_code, (
            f"expected exit {expect_code}, got {proc.returncode}\n"
            f"args={args}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc


INIT_BASE = [
    "init",
    "--task-id", "T-005",
    "--iteration", "5",
    "--phase", "construction",
    "--track", "standard",
    "--branch", "feature/T-005-openup-state-file",
    "--worktree", "/tmp/wt",
]


class OpenupStateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.state_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def state_json(self):
        with (self.state_dir / "state.json").open() as fh:
            return json.load(fh)

    # -- init -------------------------------------------------------------
    def test_init_creates_valid_file(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        data = self.state_json()
        self.assertEqual(data["schema"], 1)
        self.assertEqual(data["task_id"], "T-005")
        self.assertEqual(data["iteration"], 5)
        self.assertEqual(data["phase"], "construction")
        self.assertEqual(data["track"], "standard")
        self.assertIsNone(data["session_id"])
        self.assertTrue(data["started_at"].endswith("Z"))
        self.assertEqual(data["gates"]["plan_persisted"], False)
        self.assertEqual(data["gates"]["team_deployed"], False)
        self.assertEqual(data["iterations_since_retro"], 0)
        # validate subcommand should agree
        run(["validate"], self.state_dir, expect_code=0)

    def test_init_with_plan_seeds_gate(self):
        run(INIT_BASE + ["--plan", "docs/plans/p.md"], self.state_dir, expect_code=0)
        self.assertEqual(self.state_json()["gates"]["plan_persisted"], "docs/plans/p.md")

    def test_init_twice_without_force_errors(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        run(INIT_BASE, self.state_dir, expect_code=4)

    def test_init_force_overwrites(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        run(
            INIT_BASE + ["--force", "--iteration", "6"],
            self.state_dir,
            expect_code=0,
        )
        self.assertEqual(self.state_json()["iteration"], 6)

    # -- get --------------------------------------------------------------
    def test_get_whole(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        proc = run(["get"], self.state_dir, expect_code=0)
        self.assertEqual(json.loads(proc.stdout)["task_id"], "T-005")

    def test_get_dotted_key(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        proc = run(["get", "gates.team_deployed"], self.state_dir, expect_code=0)
        self.assertEqual(proc.stdout.strip(), "false")
        proc = run(["get", "task_id"], self.state_dir, expect_code=0)
        self.assertEqual(proc.stdout.strip(), "T-005")

    def test_get_missing_key(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        run(["get", "gates.nope"], self.state_dir, expect_code=5)

    def test_get_no_state(self):
        run(["get"], self.state_dir, expect_code=3)

    # -- set --------------------------------------------------------------
    def test_set_coercion(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        run(["set", "gates.team_deployed", "true"], self.state_dir, expect_code=0)
        self.assertIs(self.state_json()["gates"]["team_deployed"], True)
        run(["set", "iteration", "9"], self.state_dir, expect_code=0)
        self.assertEqual(self.state_json()["iteration"], 9)
        run(["set", "session_id", "null"], self.state_dir, expect_code=0)
        self.assertIsNone(self.state_json()["session_id"])
        run(["set", "session_id", "sess-abc"], self.state_dir, expect_code=0)
        self.assertEqual(self.state_json()["session_id"], "sess-abc")

    # -- set-gate ---------------------------------------------------------
    def test_set_gate_plan_path(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        run(
            ["set-gate", "plan_persisted", "docs/plans/T-005.md"],
            self.state_dir,
            expect_code=0,
        )
        self.assertEqual(
            self.state_json()["gates"]["plan_persisted"], "docs/plans/T-005.md"
        )

    # -- check-gates ------------------------------------------------------
    def test_check_gates_fails_then_passes(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        proc = run(["check-gates"], self.state_dir, expect_code=6)
        # default required set listed one per line on stderr
        for gate in ("team_deployed", "log_written", "roadmap_synced"):
            self.assertIn(gate, proc.stderr)
        for gate in ("team_deployed", "log_written", "roadmap_synced"):
            run(["set-gate", gate, "true"], self.state_dir, expect_code=0)
        run(["check-gates"], self.state_dir, expect_code=0)

    def test_check_gates_custom_require(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        # quick track: only log_written + roadmap_synced
        run(
            ["check-gates", "--require", "log_written,roadmap_synced"],
            self.state_dir,
            expect_code=6,
        )
        run(["set-gate", "log_written", "true"], self.state_dir, expect_code=0)
        run(["set-gate", "roadmap_synced", "true"], self.state_dir, expect_code=0)
        run(
            ["check-gates", "--require", "log_written,roadmap_synced"],
            self.state_dir,
            expect_code=0,
        )

    # -- archive ----------------------------------------------------------
    def test_archive_moves_and_removes(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        dest = self.state_dir / "arch" / "2026" / "state-T-005.json"
        run(["archive", str(dest)], self.state_dir, expect_code=0)
        self.assertTrue(dest.exists())
        self.assertFalse((self.state_dir / "state.json").exists())
        with dest.open() as fh:
            self.assertEqual(json.load(fh)["task_id"], "T-005")

    def test_archive_no_state(self):
        dest = self.state_dir / "x.json"
        run(["archive", str(dest)], self.state_dir, expect_code=3)

    # -- validate ---------------------------------------------------------
    def test_validate_rejects_corrupted(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        # hand-corrupt: wrong type for schema, bad enum, extra prop
        p = self.state_dir / "state.json"
        data = self.state_json()
        data["schema"] = 2  # const violation
        data["phase"] = "bogus"  # enum violation
        data["extra"] = "x"  # additionalProperties violation
        with p.open("w") as fh:
            json.dump(data, fh)
        proc = run(["validate"], self.state_dir, expect_code=7)
        self.assertIn("INVALID", proc.stderr)


if __name__ == "__main__":
    unittest.main()
