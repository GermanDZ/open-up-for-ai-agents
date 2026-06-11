#!/usr/bin/env python3
"""Unit tests for scripts/openup-claims.py (T-009).

Run with either:
    python3 -m unittest scripts.tests.test_openup_claims
    python3 scripts/tests/test_openup_claims.py

Hermetic: every test injects an isolated --claims-dir and uses --touches /
--depends-on overrides so it never depends on repo frontmatter (except the
dep-resolution tests, which deliberately use a fabricated unmet dep id).
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "openup-claims.py"

# exit codes (mirror the script)
OK, DEP, COLL, NOTFOUND, OWNER, BAD = 0, 3, 4, 5, 6, 7


def run(args, cdir, expect=None):
    cmd = [sys.executable, str(SCRIPT)] + args + ["--claims-dir", str(cdir)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if expect is not None:
        assert proc.returncode == expect, (
            f"expected exit {expect}, got {proc.returncode}\n"
            f"args={args}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc


def claim(cdir, task, touches, session="S1", deps="", expect=None):
    args = ["claim", "--task-id", task, "--session-id", session,
            "--branch", f"feature/{task}", "--worktree", f"/tmp/wt-{task}",
            "--touches", touches]
    if deps is not None:
        args += ["--depends-on", deps]
    return run(args, cdir, expect)


def preflight(cdir, task, touches, deps="", expect=None):
    args = ["preflight", "--task-id", task, "--touches", touches]
    if deps is not None:
        args += ["--depends-on", deps]
    return run(args, cdir, expect)


class ClaimTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cdir = Path(self._tmp.name) / "claims"  # deliberately absent

    def tearDown(self):
        self._tmp.cleanup()

    # --- lease lifecycle -------------------------------------------------
    def test_claim_creates_dir_and_file_with_shape(self):
        claim(self.cdir, "T-100", "src/a/", expect=OK)
        fp = self.cdir / "T-100.json"
        self.assertTrue(fp.exists(), "claims dir auto-created on first claim")
        data = json.loads(fp.read_text())
        self.assertEqual(data["task_id"], "T-100")
        self.assertEqual(data["session_id"], "S1")
        self.assertEqual(data["touches"], ["src/a/"])
        self.assertIn("claimed_at", data)
        self.assertNotIn("lease_ttl_hours", data, "claims carry NO TTL (D1)")

    def test_no_tmp_file_left_behind(self):
        claim(self.cdir, "T-100", "src/a/", expect=OK)
        leftovers = list(self.cdir.glob(".*.tmp"))
        self.assertEqual(leftovers, [], "atomic write leaves no .tmp (D3)")

    def test_release_is_idempotent(self):
        claim(self.cdir, "T-100", "src/a/", expect=OK)
        run(["release", "--task-id", "T-100"], self.cdir, expect=OK)
        self.assertFalse((self.cdir / "T-100.json").exists())
        run(["release", "--task-id", "T-100"], self.cdir, expect=OK)  # again: no error

    def test_get_missing_claim(self):
        run(["get", "--task-id", "T-404"], self.cdir, expect=NOTFOUND)

    # --- collision (T-008 D2 path-segment-prefix) ------------------------
    def test_collision_prefix_on_boundary(self):
        claim(self.cdir, "T-100", "docs/changes/", expect=OK)
        p = preflight(self.cdir, "T-200", "docs/changes/T-002/", expect=COLL)
        self.assertIn("T-100", p.stderr)
        self.assertIn("S1", p.stderr)  # owning session named (R4: substring)

    def test_no_collision_distinct_segment(self):
        claim(self.cdir, "T-100", "docs/changes/", expect=OK)
        preflight(self.cdir, "T-200", "docs/changesets/", expect=OK)

    def test_collision_identical_path(self):
        claim(self.cdir, "T-100", "a/b", expect=OK)
        preflight(self.cdir, "T-200", "a/b", expect=COLL)

    def test_parent_blocks_child(self):
        claim(self.cdir, "T-100", "a/", expect=OK)
        preflight(self.cdir, "T-200", "a/b/c/", expect=COLL)

    # --- Q2: empty touches = no collide ----------------------------------
    def test_empty_touches_no_collision(self):
        claim(self.cdir, "T-100", "docs/changes/", expect=OK)
        preflight(self.cdir, "T-200", "", expect=OK)  # claimant declares nothing
        # and a prior empty-touches claim blocks nobody:
        claim(self.cdir, "T-050", "", expect=OK)
        preflight(self.cdir, "T-300", "docs/changes/", expect=COLL)  # only T-100 blocks

    # --- D1: claims never expire (any present claim blocks) --------------
    def test_existing_claim_always_blocks(self):
        claim(self.cdir, "T-100", "lib/x/", expect=OK)
        # No age path exists; the claim blocks purely by presence.
        preflight(self.cdir, "T-200", "lib/x/y/", expect=COLL)

    # --- Q4: dependencies checked before collision -----------------------
    def test_unmet_dep_reported_before_collision(self):
        # T-100 owns the surface; T-200 would BOTH collide AND have an unmet dep.
        claim(self.cdir, "T-100", "docs/changes/", expect=OK)
        p = preflight(self.cdir, "T-200", "docs/changes/", deps="T-999", expect=DEP)
        self.assertIn("dependency", p.stderr.lower())
        self.assertIn("T-999", p.stderr)
        self.assertNotIn("COLLISION", p.stderr, "dep checked first; collision not reached")

    def test_no_deps_proceeds(self):
        preflight(self.cdir, "T-200", "x/", deps="", expect=OK)

    # --- ownership / idempotency -----------------------------------------
    def test_same_session_reclaim_ok(self):
        claim(self.cdir, "T-100", "a/", session="S1", expect=OK)
        claim(self.cdir, "T-100", "a/", session="S1", expect=OK)  # idempotent

    def test_different_session_reclaim_refused(self):
        claim(self.cdir, "T-100", "a/", session="S1", expect=OK)
        p = claim(self.cdir, "T-100", "a/", session="S2", expect=OWNER)
        self.assertIn("S1", p.stderr)

    def test_self_does_not_collide(self):
        # Re-claiming own task must not flag its own surface as a collision.
        claim(self.cdir, "T-100", "a/b/", session="S1", expect=OK)
        claim(self.cdir, "T-100", "a/b/", session="S1", expect=OK)

    # --- TC-EDGE-05: corrupt claim file is fail-closed (D8) ---------------
    def test_corrupt_claim_blocks_failclosed(self):
        claim(self.cdir, "T-100", "a/", expect=OK)
        (self.cdir / "T-300.json").write_text("{ not json", encoding="utf-8")
        # Even a totally disjoint surface is refused while a corrupt claim exists.
        p = preflight(self.cdir, "T-200", "z/totally/disjoint/", expect=COLL)
        self.assertIn("T-300", p.stderr)
        self.assertIn("fail-closed", p.stderr.lower())

    # --- list reflects live claims ---------------------------------------
    def test_list_reflects_claims(self):
        claim(self.cdir, "T-100", "a/", expect=OK)
        claim(self.cdir, "T-101", "b/", expect=OK)
        out = run(["list"], self.cdir, expect=OK).stdout
        ids = {c["task_id"] for c in json.loads(out)}
        self.assertEqual(ids, {"T-100", "T-101"})


if __name__ == "__main__":
    unittest.main()
