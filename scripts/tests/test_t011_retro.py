#!/usr/bin/env python3
"""Unit tests for the T-011 retro-cadence counter (`openup-state.py retro`).

Covers the durable counter in `.openup/retro.json` and its three lifecycle
actions (increment / reset / check) plus the live-state mirroring, driven
through the CLI exactly as the skills drive it.

Run with either:
    python3 -m unittest scripts.tests.test_t011_retro
    python3 scripts/tests/test_t011_retro.py
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "openup-state.py"

INIT_BASE = [
    "init",
    "--task-id", "T-011",
    "--iteration", "8",
    "--phase", "construction",
    "--track", "standard",
    "--branch", "feature/T-011-retro-cadence-handoff",
    "--worktree", "/tmp/wt",
]


def run(args, state_dir, expect_code=None):
    cmd = [sys.executable, str(SCRIPT)] + args + ["--state-dir", str(state_dir)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if expect_code is not None:
        assert proc.returncode == expect_code, (
            f"expected exit {expect_code}, got {proc.returncode}\n"
            f"args={args}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc


class RetroCadenceTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.state_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def retro_json(self):
        with (self.state_dir / "retro.json").open() as fh:
            return json.load(fh)

    def state_json(self):
        with (self.state_dir / "state.json").open() as fh:
            return json.load(fh)

    # -- get defaults to 0 when no file exists ---------------------------
    def test_get_defaults_to_zero(self):
        out = run(["retro", "get"], self.state_dir, expect_code=0).stdout.strip()
        self.assertEqual(out, "0")

    # -- increment accumulates and survives without a state file ---------
    def test_increment_accumulates(self):
        self.assertEqual(run(["retro", "increment"], self.state_dir, 0).stdout.strip(), "1")
        self.assertEqual(run(["retro", "increment"], self.state_dir, 0).stdout.strip(), "2")
        self.assertEqual(run(["retro", "increment"], self.state_dir, 0).stdout.strip(), "3")
        self.assertEqual(self.retro_json()["iterations_since_retro"], 3)
        # No state file present -> increment must still work (the carry-forward case).
        self.assertFalse((self.state_dir / "state.json").exists())

    # -- increment survives an archive (the core carry-forward guarantee) -
    def test_counter_survives_archive(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        run(["retro", "increment"], self.state_dir, expect_code=0)
        run(["retro", "increment"], self.state_dir, expect_code=0)
        dest = self.state_dir / "archived-state.json"
        run(["archive", str(dest)], self.state_dir, expect_code=0)
        self.assertFalse((self.state_dir / "state.json").exists())  # archive removed state
        # retro.json is untouched by archive:
        self.assertEqual(run(["retro", "get"], self.state_dir, 0).stdout.strip(), "2")

    # -- check below threshold: ok, retro_due stays false ----------------
    def test_check_below_threshold(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        for _ in range(4):
            run(["retro", "increment"], self.state_dir, expect_code=0)
        out = run(["retro", "check"], self.state_dir, expect_code=0).stdout.strip()
        self.assertEqual(out, "ok 4")
        self.assertFalse(self.state_json()["gates"]["retro_due"])
        self.assertEqual(self.state_json()["iterations_since_retro"], 4)

    # -- check at/above threshold: due, retro_due set true, mirror synced -
    def test_check_at_threshold_sets_gate(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        for _ in range(5):
            run(["retro", "increment"], self.state_dir, expect_code=0)
        out = run(["retro", "check"], self.state_dir, expect_code=0).stdout.strip()
        self.assertEqual(out, "due 5")
        self.assertTrue(self.state_json()["gates"]["retro_due"])
        self.assertEqual(self.state_json()["iterations_since_retro"], 5)

    # -- custom threshold flag -------------------------------------------
    def test_check_custom_threshold(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        run(["retro", "increment"], self.state_dir, expect_code=0)
        run(["retro", "increment"], self.state_dir, expect_code=0)
        out = run(["retro", "check", "--threshold", "2"], self.state_dir, 0).stdout.strip()
        self.assertEqual(out, "due 2")
        self.assertTrue(self.state_json()["gates"]["retro_due"])

    # -- check with no live state still reports (no crash) ---------------
    def test_check_without_state_file(self):
        run(["retro", "increment"], self.state_dir, expect_code=0)
        out = run(["retro", "check", "--threshold", "1"], self.state_dir, 0).stdout.strip()
        self.assertEqual(out, "due 1")
        self.assertFalse((self.state_dir / "state.json").exists())

    # -- reset zeroes the counter and clears the gate --------------------
    def test_reset_clears_counter_and_gate(self):
        run(INIT_BASE, self.state_dir, expect_code=0)
        for _ in range(6):
            run(["retro", "increment"], self.state_dir, expect_code=0)
        run(["retro", "check"], self.state_dir, expect_code=0)
        self.assertTrue(self.state_json()["gates"]["retro_due"])
        run(["retro", "reset"], self.state_dir, expect_code=0)
        self.assertEqual(self.retro_json()["iterations_since_retro"], 0)
        self.assertEqual(run(["retro", "get"], self.state_dir, 0).stdout.strip(), "0")
        self.assertFalse(self.state_json()["gates"]["retro_due"])
        self.assertEqual(self.state_json()["iterations_since_retro"], 0)

    # -- reset between iterations (no live state) does not crash ---------
    def test_reset_without_state_file(self):
        run(["retro", "increment"], self.state_dir, expect_code=0)
        run(["retro", "reset"], self.state_dir, expect_code=0)
        self.assertEqual(run(["retro", "get"], self.state_dir, 0).stdout.strip(), "0")

    # -- the seed-on-init mirror flow (start-iteration carry-forward) ----
    def test_seed_on_init_from_durable_count(self):
        # Simulate three completed iterations accruing the durable counter.
        for _ in range(3):
            run(["retro", "increment"], self.state_dir, expect_code=0)
        # start-iteration seeds the new state from `retro get`.
        seed = run(["retro", "get"], self.state_dir, 0).stdout.strip()
        run(INIT_BASE + ["--iterations-since-retro", seed], self.state_dir, expect_code=0)
        self.assertEqual(self.state_json()["iterations_since_retro"], 3)
        # state is still schema-valid with the seeded mirror.
        run(["validate"], self.state_dir, expect_code=0)


if __name__ == "__main__":
    unittest.main()
