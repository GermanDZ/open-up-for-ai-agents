#!/usr/bin/env python3
"""Unit tests for scripts/openup-session.py + the board reap wiring (T-063).

Run:
    python3 -m unittest scripts.tests.test_openup_session
    python3 scripts/tests/test_openup_session.py

Every test is hermetic: isolated --claims-dir / --state-dir / --log-dir under a
tmp dir, and --no-push so no git-ref network op runs. Subprocess invocation (not
in-process import) mirrors test_openup_claims.py and avoids module-state bleed.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
SESSION = SCRIPTS / "openup-session.py"
BOARD = SCRIPTS / "openup-board.py"
CLAIMS = SCRIPTS / "openup-claims.py"


def run(script, args, expect=None):
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, cwd=str(SCRIPTS.parent),
    )
    if expect is not None:
        assert proc.returncode == expect, (
            f"expected rc={expect}, got {proc.returncode}\n"
            f"stdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc


def begin_args(tmp, task="TEST-1", touches="scripts/foo.py", extra=None):
    a = [
        "begin", "--task-id", task, "--session-id", "s1",
        "--branch", "b1", "--worktree", "/tmp/wt",
        "--iteration", "1", "--phase", "construction", "--track", "standard",
        "--touches", touches, "--goal", "test", "--no-push",
        "--claims-dir", str(tmp / "claims"),
        "--state-dir", str(tmp / "state"),
        "--log-dir", str(tmp / "logs"),
    ]
    return a + (extra or [])


def seed_claim(cdir: Path, task: str, heartbeat=None):
    cdir.mkdir(parents=True, exist_ok=True)
    payload = {"task_id": task, "session_id": "s"}
    if heartbeat:
        payload["last_heartbeat"] = heartbeat
    (cdir / f"{task}.json").write_text(json.dumps(payload))


class TestBeginEnd(unittest.TestCase):
    def test_clean_begin_creates_claim_state_log(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            proc = run(SESSION, begin_args(tmp), expect=0)
            out = json.loads(proc.stdout.strip())
            self.assertTrue(out["claimed"])
            self.assertEqual(out["task"], "TEST-1")
            # claim + state + log all exist
            self.assertTrue((tmp / "claims" / "TEST-1.json").exists())
            state = json.loads((tmp / "state" / "state.json").read_text())
            self.assertEqual(state["task_id"], "TEST-1")
            shards = list((tmp / "logs" / "runs").glob("*.jsonl"))
            self.assertEqual(len(shards), 1)
            self.assertIn("session_begin", shards[0].read_text())

    def test_end_archives_releases_and_logs(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            run(SESSION, begin_args(tmp), expect=0)
            arch = tmp / "arch.json"
            run(SESSION, [
                "end", "--task-id", "TEST-1", "--archive-to", str(arch),
                "--branch", "b1", "--no-push",
                "--claims-dir", str(tmp / "claims"),
                "--state-dir", str(tmp / "state"),
                "--log-dir", str(tmp / "logs"),
            ], expect=0)
            self.assertTrue(arch.exists())                                   # archived
            self.assertFalse((tmp / "state" / "state.json").exists())        # live gone
            self.assertFalse((tmp / "claims" / "TEST-1.json").exists())      # released
            self.assertIn("session_end",
                          (tmp / "logs" / "runs").glob("*.jsonl").__next__().read_text())

    def test_begin_rolls_back_claim_on_post_claim_failure(self):
        # Pre-create a state.json so state-init fails AFTER the claim is written.
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "state").mkdir(parents=True)
            preexisting = tmp / "state" / "state.json"
            preexisting.write_text('{"schema":1,"owner":"other-session"}')
            proc = run(SESSION, begin_args(tmp, task="TEST-2", touches="scripts/bar.py"))
            self.assertNotEqual(proc.returncode, 0)                          # begin failed
            # claim taken mid-begin was rolled back (Requirement 2):
            self.assertFalse((tmp / "claims" / "TEST-2.json").exists())
            # a pre-existing state.json (another session's) must NOT be deleted:
            self.assertTrue(preexisting.exists())
            self.assertIn("other-session", preexisting.read_text())


class TestBoardReapWiring(unittest.TestCase):
    def _refresh(self, tmp, extra=None):
        return run(BOARD, [
            "refresh", "--root", str(tmp),
            "--claims-dir", str(tmp / "claims"),
            "--out", str(tmp / "board.json"),
        ] + (extra or []))

    def test_refresh_reaps_stale_keeps_no_heartbeat(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            cdir = tmp / "claims"
            seed_claim(cdir, "STALE-1", heartbeat="2000-01-01T00:00:00Z")
            seed_claim(cdir, "NOHB-1")  # no heartbeat -> T-060 invariant: never reaped
            proc = self._refresh(tmp)
            self.assertEqual(proc.returncode, 0)
            # stdout must be clean board JSON (reaper chatter went to stderr)
            json.loads(proc.stdout.strip())
            self.assertFalse((cdir / "STALE-1.json").exists())  # reaped
            self.assertTrue((cdir / "NOHB-1.json").exists())    # kept (invariant)

    def test_no_reap_flag_keeps_stale(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            cdir = tmp / "claims"
            seed_claim(cdir, "STALE-2", heartbeat="2000-01-01T00:00:00Z")
            self._refresh(tmp, extra=["--no-reap"])
            self.assertTrue((cdir / "STALE-2.json").exists())   # not reaped


if __name__ == "__main__":
    unittest.main()
