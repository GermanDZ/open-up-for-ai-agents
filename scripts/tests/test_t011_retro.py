#!/usr/bin/env python3
"""Unit tests for the T-011 retro-cadence counter (`openup-state.py retro`).

Covers the durable counter at `<git-common-dir>/openup/retro.json` and its
lifecycle actions (increment / reset / check) plus the live-state mirroring,
driven through the CLI exactly as the skills drive it. `RetroCadenceTests`
covers the counter's behaviour (including T-142's archive-advances-the-cadence
rule); `RetroStorageLocationTests` covers T-143's worktree-shared storage.

Run with either:
    python3 -m unittest scripts.tests.test_t011_retro
    python3 scripts/tests/test_t011_retro.py
"""

import json
import os
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
        """The counter outlives the state file `archive` deletes. Since T-142
        `archive` also *advances* it (it is the completion event), so the
        carry-forward guarantee is now "survives and increments", not
        "untouched"."""
        run(INIT_BASE, self.state_dir, expect_code=0)
        run(["retro", "increment"], self.state_dir, expect_code=0)
        run(["retro", "increment"], self.state_dir, expect_code=0)
        dest = self.state_dir / "archived-state.json"
        run(["archive", str(dest)], self.state_dir, expect_code=0)
        self.assertFalse((self.state_dir / "state.json").exists())  # archive removed state
        # retro.json survived the archive, and the archive counted as a completion:
        self.assertEqual(run(["retro", "get"], self.state_dir, 0).stdout.strip(), "3")

    # -- archive advances the cadence on EVERY track (T-142) --------------
    def test_archive_advances_cadence(self):
        """T-142: the increment lives in `archive` — the one teardown step every
        completion path runs — so a quick-track lane counts like any other. It
        used to be prose in `/openup-complete-task` only, which is why quick
        lanes silently advanced nothing."""
        run(INIT_BASE, self.state_dir, expect_code=0)
        proc = run(
            ["archive", str(self.state_dir / "archived-state.json")],
            self.state_dir,
            expect_code=0,
        )
        self.assertIn("Retro cadence: 1", proc.stdout)
        self.assertEqual(self.retro_json()["iterations_since_retro"], 1)

    def test_failed_archive_does_not_advance_cadence(self):
        """Exit 3 (no state) must leave the count alone, so a repeated or
        mistaken archive can never inflate the cadence."""
        run(["retro", "increment"], self.state_dir, expect_code=0)
        run(["archive", str(self.state_dir / "x.json")], self.state_dir, expect_code=3)
        self.assertEqual(run(["retro", "get"], self.state_dir, 0).stdout.strip(), "1")

    def test_archive_no_retro_suppresses_increment(self):
        run(["retro", "increment"], self.state_dir, expect_code=0)
        run(INIT_BASE, self.state_dir, expect_code=0)
        dest = self.state_dir / "archived-state.json"
        proc = run(["archive", str(dest), "--no-retro"], self.state_dir, expect_code=0)
        self.assertNotIn("Retro cadence", proc.stdout)
        self.assertEqual(run(["retro", "get"], self.state_dir, 0).stdout.strip(), "1")
        # --no-retro changes only the cadence, never the archive itself:
        self.assertTrue(dest.exists())
        self.assertFalse((self.state_dir / "state.json").exists())

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


class RetroStorageLocationTests(unittest.TestCase):
    """T-143: the counter must live somewhere every worktree of a clone shares.

    These tests copy the CLI into a throwaway git repo and drive it there, so
    they exercise the real `git rev-parse --git-common-dir` resolution without
    ever touching the developer's own <git-common-dir>/openup/retro.json.
    """

    SCHEMA = SCRIPT.parent / "openup-state.schema.json"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def plant(self, root: Path) -> Path:
        """Copy the CLI (+ its schema) into root/scripts; return the CLI path."""
        (root / "scripts").mkdir(parents=True, exist_ok=True)
        for src in (SCRIPT, self.SCHEMA):
            (root / "scripts" / src.name).write_bytes(src.read_bytes())
        return root / "scripts" / SCRIPT.name

    def git(self, *args, cwd):
        proc = subprocess.run(
            ["git", *args], cwd=str(cwd), capture_output=True, text=True,
            env={**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null",
                 "GIT_CONFIG_SYSTEM": "/dev/null"},
        )
        assert proc.returncode == 0, f"git {args} failed: {proc.stderr}"
        return proc

    def make_repo(self) -> Path:
        repo = self.tmp / "repo"
        repo.mkdir()
        self.git("init", "-q", "-b", "main", cwd=repo)
        self.git("config", "user.email", "t@example.com", cwd=repo)
        self.git("config", "user.name", "T", cwd=repo)
        self.plant(repo)
        self.git("add", "-A", cwd=repo)
        self.git("commit", "-qm", "seed", cwd=repo)
        return repo

    def cli(self, cli_path: Path, *args) -> str:
        proc = subprocess.run(
            [sys.executable, str(cli_path), *args], capture_output=True, text=True,
        )
        assert proc.returncode == 0, f"{args} -> {proc.returncode}: {proc.stderr}"
        return proc.stdout.strip()

    # -- default location is the shared git common dir --------------------
    def test_default_location_is_git_common_dir(self):
        repo = self.make_repo()
        cli = repo / "scripts" / SCRIPT.name
        self.assertEqual(self.cli(cli, "retro", "increment"), "1")
        self.assertTrue((repo / ".git" / "openup" / "retro.json").exists())
        # NOT the old per-worktree location:
        self.assertFalse((repo / ".openup" / "retro.json").exists())

    # -- the whole point: two worktrees, one count ------------------------
    def test_two_worktrees_share_one_count(self):
        repo = self.make_repo()
        cli = repo / "scripts" / SCRIPT.name
        self.cli(cli, "retro", "increment")  # -> 1 in the main worktree

        wt = self.tmp / "repo-lane"
        self.git("worktree", "add", "-q", str(wt), "-b", "lane", cwd=repo)
        wt_cli = wt / "scripts" / SCRIPT.name
        self.assertTrue(wt_cli.exists())  # scripts/ is committed, so the lane has it

        # The fresh worktree sees the count the previous lane left behind...
        self.assertEqual(self.cli(wt_cli, "retro", "get"), "1")
        # ...and its own increment is visible back in the main worktree.
        self.assertEqual(self.cli(wt_cli, "retro", "increment"), "2")
        self.assertEqual(self.cli(cli, "retro", "get"), "2")

    # -- override precedence ----------------------------------------------
    def test_retro_dir_overrides_state_dir_and_shared_default(self):
        repo = self.make_repo()
        cli = repo / "scripts" / SCRIPT.name
        override = self.tmp / "elsewhere"
        state = self.tmp / "state"
        self.cli(cli, "retro", "increment",
                 "--retro-dir", str(override), "--state-dir", str(state))
        self.assertTrue((override / "retro.json").exists())
        self.assertFalse((state / "retro.json").exists())
        self.assertFalse((repo / ".git" / "openup" / "retro.json").exists())

    def test_state_dir_scopes_counter_when_no_retro_dir(self):
        """Isolation guarantee: a --state-dir caller (every test in this file,
        and any deliberately-isolated run) must not touch the shared counter."""
        repo = self.make_repo()
        cli = repo / "scripts" / SCRIPT.name
        state = self.tmp / "state"
        self.cli(cli, "retro", "increment", "--state-dir", str(state))
        self.assertTrue((state / "retro.json").exists())
        self.assertFalse((repo / ".git" / "openup" / "retro.json").exists())

    # -- read-forward migration -------------------------------------------
    def test_legacy_count_is_carried_forward_once(self):
        repo = self.make_repo()
        cli = repo / "scripts" / SCRIPT.name
        legacy = repo / ".openup"
        legacy.mkdir()
        (legacy / "retro.json").write_text('{"iterations_since_retro": 3}\n')

        # Carried forward, not reset to 0:
        self.assertEqual(self.cli(cli, "retro", "get"), "3")
        # The first write lands at the shared path and seeds from the legacy value:
        self.assertEqual(self.cli(cli, "retro", "increment"), "4")
        self.assertTrue((repo / ".git" / "openup" / "retro.json").exists())
        # Non-destructive: the legacy file is left exactly as it was...
        self.assertEqual(
            json.loads((legacy / "retro.json").read_text())["iterations_since_retro"], 3
        )
        # ...and is never re-applied now that the shared file exists.
        self.assertEqual(self.cli(cli, "retro", "get"), "4")

    # -- fail-open outside a git repo -------------------------------------
    def test_non_git_checkout_falls_back_to_repo_local_openup(self):
        """The cadence is advisory: no git, no crash — just the old location."""
        root = self.tmp / "not-a-repo"
        root.mkdir()
        cli = self.plant(root)
        self.assertEqual(self.cli(cli, "retro", "increment"), "1")
        self.assertTrue((root / ".openup" / "retro.json").exists())


if __name__ == "__main__":
    unittest.main()
