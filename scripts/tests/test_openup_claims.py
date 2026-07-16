#!/usr/bin/env python3
"""Unit tests for scripts/openup-claims.py (T-009).

Run with either:
    python3 -m unittest scripts.tests.test_openup_claims
    python3 scripts/tests/test_openup_claims.py

Hermetic: every test injects an isolated --claims-dir and uses --touches /
--depends-on overrides so it never depends on repo frontmatter (except the
dep-resolution tests, which deliberately use a fabricated unmet dep id).
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "openup-claims.py"

# Load the module directly for unit-level tests of pure functions (roadmap_status).
_spec = importlib.util.spec_from_file_location("openup_claims_under_test", SCRIPT)
claims_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(claims_mod)

# exit codes (mirror the script)
OK, DEP, COLL, NOTFOUND, OWNER, BAD = 0, 3, 4, 5, 6, 7


def run(args, cdir, expect=None):
    """Run an openup-claims.py subcommand with an isolated claims dir.

    --no-push is injected automatically for every invocation so existing tests
    remain hermetic even after git-ref locking was added (the git-ref path
    requires a real remote and is tested separately in GitRefClaimTests).
    The --no-push flag is only injected for subcommands that accept it.
    """
    _NO_PUSH_CMDS = {"claim", "release", "preflight", "remote-check"}
    cmd = [sys.executable, str(SCRIPT)] + args + ["--claims-dir", str(cdir)]
    # Inject --no-push before any existing --no-push to avoid duplicates.
    if args and args[0] in _NO_PUSH_CMDS and "--no-push" not in args:
        cmd = [sys.executable, str(SCRIPT)] + args + [
            "--claims-dir", str(cdir), "--no-push"
        ]
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


class IdReservationTests(unittest.TestCase):
    """T-031: task-ID allocation through the claims mechanism.

    Hermetic: a fabricated repo root (roadmap + change folders, NOT a git
    repo, so the origin/main scan is a silent no-op) plus an isolated
    claims dir, both injected via --repo-root / --claims-dir.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.cdir = base / "claims"
        self.root = base / "repo"
        # Roadmap mentions T-007 with no plan folder (maintenance-row case);
        # a change folder holds T-005.
        (self.root / "docs").mkdir(parents=True)
        (self.root / "docs" / "roadmap.md").write_text(
            "| T-007 | roadmap-only task | pending |\n", encoding="utf-8"
        )
        plan = self.root / "docs" / "changes" / "T-005"
        plan.mkdir(parents=True)
        (plan / "plan.md").write_text(
            "---\nid: T-005\ntitle: x\n---\n", encoding="utf-8"
        )

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, args, expect=None):
        if args[0] in ("next-id", "reserve-id"):  # only these scan the repo
            args = args + ["--repo-root", str(self.root)]
        return run(args, self.cdir, expect)

    def reserve(self, session="S1", extra=None, expect=None):
        return self._run(
            ["reserve-id", "--session-id", session] + (extra or []), expect
        )

    # --- allocation sources -----------------------------------------------
    def test_next_id_unions_roadmap_and_change_folders(self):
        # Highest used is T-007 (roadmap text), not T-005 (frontmatter).
        p = self._run(["next-id"], expect=OK)
        self.assertEqual(p.stdout.strip(), "T-008")

    def test_next_id_writes_nothing(self):
        self._run(["next-id"], expect=OK)
        self.assertFalse((self.cdir / "ids").exists())

    def test_reserve_skips_live_reservations(self):
        self.assertEqual(self.reserve(expect=OK).stdout.strip(), "T-008")
        self.assertEqual(self.reserve(expect=OK).stdout.strip(), "T-009")

    def test_reservation_file_shape(self):
        self.reserve(extra=["--title", "my task"], expect=OK)
        data = json.loads((self.cdir / "ids" / "T-008.json").read_text())
        self.assertEqual(data["task_id"], "T-008")
        self.assertEqual(data["session_id"], "S1")
        self.assertEqual(data["title"], "my task")
        self.assertIn("reserved_at", data)

    def test_no_tmp_left_behind(self):
        self.reserve(expect=OK)
        self.assertEqual(list((self.cdir / "ids").glob(".*.tmp")), [])

    # --- explicit ID ------------------------------------------------------
    def test_explicit_id_used_in_repo_refused(self):
        p = self.reserve(extra=["--task-id", "T-007"], expect=OWNER)
        self.assertIn("already in use", p.stderr)

    def test_explicit_id_other_session_refused_same_session_idempotent(self):
        self.reserve(extra=["--task-id", "T-050"], expect=OK)
        self.reserve(session="S1", extra=["--task-id", "T-050"], expect=OK)
        p = self.reserve(session="S2", extra=["--task-id", "T-050"], expect=OWNER)
        self.assertIn("S1", p.stderr)

    def test_explicit_id_malformed_refused(self):
        self.reserve(extra=["--task-id", "TASK-9"], expect=BAD)

    # --- release ----------------------------------------------------------
    def test_release_id_idempotent_and_frees_the_id(self):
        self.reserve(expect=OK)  # T-008
        self._run(["release-id", "--task-id", "T-008"], expect=OK)
        self._run(["release-id", "--task-id", "T-008"], expect=OK)
        self.assertEqual(self.reserve(expect=OK).stdout.strip(), "T-008")

    # --- prefix / pad -----------------------------------------------------
    def test_prefix_namespaces_are_independent(self):
        p = self.reserve(extra=["--prefix", "C3-"], expect=OK)
        self.assertEqual(p.stdout.strip(), "C3-001")
        # T- namespace unaffected by the C3- reservation.
        self.assertEqual(self.reserve(expect=OK).stdout.strip(), "T-008")

    def test_pad_width(self):
        p = self.reserve(extra=["--prefix", "C3-", "--pad", "2"], expect=OK)
        self.assertEqual(p.stdout.strip(), "C3-01")

    # --- the race itself --------------------------------------------------
    def test_concurrent_reservations_get_distinct_ids(self):
        # N processes race from the same starting scan; every one must end
        # up with a unique ID (the exclusive-create loop absorbs the race).
        n = 8
        cmd = [sys.executable, str(SCRIPT), "reserve-id",
               "--session-id", "RACE", "--repo-root", str(self.root),
               "--claims-dir", str(self.cdir)]
        procs = [subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
                 for _ in range(n)]
        ids = [p.communicate()[0].strip() for p in procs]
        self.assertTrue(all(p.returncode == 0 for p in procs))
        self.assertEqual(len(set(ids)), n, f"duplicate IDs allocated: {ids}")

    # --- list-ids ---------------------------------------------------------
    def test_list_ids_reflects_reservations(self):
        self.reserve(expect=OK)
        self.reserve(expect=OK)
        out = self._run(["list-ids"], expect=OK).stdout
        ids = {r["task_id"] for r in json.loads(out)}
        self.assertEqual(ids, {"T-008", "T-009"})

    def test_reservations_invisible_to_claim_list(self):
        # An ID reservation must never read as a surface claim.
        self.reserve(expect=OK)
        out = run(["list"], self.cdir, expect=OK).stdout
        self.assertEqual(json.loads(out), [])


# exit code added by T-044
REMOTE_DUP = 9


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=str(repo),
                   capture_output=True, text=True, check=True)


def run_rc(repo, args, expect=None):
    """Run a subcommand with cwd inside ``repo`` (no --claims-dir injected)."""
    proc = subprocess.run([sys.executable, str(SCRIPT)] + args,
                          cwd=str(repo), capture_output=True, text=True)
    if expect is not None:
        assert proc.returncode == expect, (
            f"expected exit {expect}, got {proc.returncode}\n"
            f"args={args}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc


class RemoteCheckTests(unittest.TestCase):
    """T-044 — advisory cross-machine branch-as-claim preflight."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.remote = self.tmp / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(self.remote)],
                       check=True)
        self.local = self.tmp / "local"
        self.local.mkdir()
        _git(self.local, "init", "-q")
        _git(self.local, "config", "user.email", "t@t")
        _git(self.local, "config", "user.name", "t")
        (self.local / "f.txt").write_text("x")
        _git(self.local, "add", "-A")
        _git(self.local, "commit", "-qm", "init")
        _git(self.local, "branch", "-M", "main")
        _git(self.local, "remote", "add", "origin", str(self.remote))
        _git(self.local, "push", "-q", "origin", "main")

    def tearDown(self):
        self._tmp.cleanup()

    def _push_branch(self, name):
        _git(self.local, "checkout", "-q", "-b", name)
        _git(self.local, "push", "-q", "origin", name)
        _git(self.local, "checkout", "-q", "main")

    def test_remote_duplicate_refused(self):
        self._push_branch("fix/T-044-other")
        run_rc(self.local,
               ["remote-check", "--task-id", "T-044", "--no-fetch",
                "--self-branch", "feature/T-044-mine"],
               expect=REMOTE_DUP)

    def test_no_match_is_ready(self):
        self._push_branch("feature/T-099-unrelated")
        p = run_rc(self.local,
                   ["remote-check", "--task-id", "T-044", "--no-fetch"],
                   expect=OK)
        self.assertIn("READY", p.stdout)

    def test_self_branch_excluded(self):
        # the only matching remote branch is OUR lane → not a collision
        self._push_branch("feature/T-044-mine")
        run_rc(self.local,
               ["remote-check", "--task-id", "T-044", "--no-fetch",
                "--self-branch", "feature/T-044-mine"],
               expect=OK)

    def test_token_accuracy_no_false_positive(self):
        # T-44 (no leading zero) must not match T-044
        self._push_branch("fix/T-44-x")
        run_rc(self.local,
               ["remote-check", "--task-id", "T-044", "--no-fetch"],
               expect=OK)

    def test_missing_remote_fails_open(self):
        noremote = self.tmp / "noremote"
        noremote.mkdir()
        _git(noremote, "init", "-q")
        _git(noremote, "config", "user.email", "t@t")
        _git(noremote, "config", "user.name", "t")
        (noremote / "f.txt").write_text("x")
        _git(noremote, "add", "-A")
        _git(noremote, "commit", "-qm", "init")
        p = run_rc(noremote,
                   ["remote-check", "--task-id", "T-044", "--no-fetch"],
                   expect=OK)
        self.assertIn("advisory", (p.stdout + p.stderr).lower())


def _write(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _plan(tid, status):
    return f"---\nid: {tid}\nstatus: {status}\ntouches: []\ndepends-on: []\n---\n# {tid}\n"


def _roadmap(rows):
    # Canonical roadmap table — the `| ID | …` header the shared parser
    # (openup-roadmap.py parse_roadmap, reused by roadmap_status per T-122/B9)
    # requires; every real roadmap uses it.
    out = ["# Roadmap", "", "| ID | Title | Status | Priority |", "|---|---|---|---|"]
    for tid, status_cell in rows:
        out.append(f"| [{tid}](changes/archive/{tid}/plan.md) | t | {status_cell} | high |")
    return "\n".join(out) + "\n"


def _roadmap_prose(rows):
    # Prose `## T-NNN:` section roadmap (the shape this repo's own roadmap uses
    # below its maintenance table) — table-only roadmap_status returned None here
    # before T-122/B9.
    out = ["# Roadmap", ""]
    for tid, status in rows:
        out += [f"## {tid}: sample task", f"**Status**: {status}",
                "**Priority**: high", "**Dependencies**: none", ""]
    return "\n".join(out) + "\n"


class RoadmapStatusTests(unittest.TestCase):
    """T-122/B9 — roadmap_status reads BOTH table rows and prose ## T-NNN:
    sections, via openup-roadmap.py's shared parser (no drift)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _status(self, tid):
        return claims_mod.roadmap_status(tid, self.root)

    def test_prose_section_status_resolved(self):
        _write(self.root / "docs/roadmap.md",
               _roadmap_prose([("T-050", "completed (2026-07-05)")]))
        self.assertEqual(self._status("T-050"), "completed")

    def test_prose_section_pending_resolved(self):
        _write(self.root / "docs/roadmap.md", _roadmap_prose([("T-051", "pending")]))
        self.assertEqual(self._status("T-051"), "pending")

    def test_table_row_status_still_resolved(self):
        _write(self.root / "docs/roadmap.md",
               _roadmap([("T-052", "completed (2026-01-01)")]))
        self.assertEqual(self._status("T-052"), "completed")

    def test_missing_id_returns_none(self):
        _write(self.root / "docs/roadmap.md", _roadmap([("T-052", "completed")]))
        self.assertIsNone(self._status("T-999"))

    def test_no_roadmap_returns_none(self):
        self.assertIsNone(self._status("T-050"))

    def test_exact_id_match_not_substring(self):
        # Old substring scan would match "T-1" inside a "T-12" row; the shared
        # parser matches ids exactly.
        _write(self.root / "docs/roadmap.md", _roadmap([("T-12", "completed")]))
        self.assertIsNone(self._status("T-1"))
        self.assertEqual(self._status("T-12"), "completed")


class ArchivedDepTests(unittest.TestCase):
    """T-048 — archived plans defer to the roadmap; stale-status migration."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.cdir = self.root / ".claims"

    def tearDown(self):
        self._tmp.cleanup()

    def _pf(self, dep, expect):
        return run(["preflight", "--task-id", "SCRATCH", "--touches", "x/y",
                    "--depends-on", dep, "--repo-root", str(self.root)],
                   self.cdir, expect)

    def _mig(self, *extra, expect=OK):
        cmd = [sys.executable, str(SCRIPT), "migrate-archived-status",
               "--repo-root", str(self.root), *extra]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if expect is not None:
            assert proc.returncode == expect, (
                f"expected {expect}, got {proc.returncode}\n{proc.stdout}\n{proc.stderr}")
        return proc

    # --- dep_satisfied (Req 2) ---
    def test_archived_stale_but_roadmap_completed_is_satisfied(self):
        _write(self.root / "docs/changes/archive/T-900/plan.md", _plan("T-900", "in-progress"))
        _write(self.root / "docs/roadmap.md", _roadmap([("T-900", "completed (2026-01-01)")]))
        self.assertIn("READY", self._pf("T-900", OK).stdout)

    def test_archived_stale_but_PROSE_roadmap_completed_is_satisfied(self):
        # T-122/B9 — the T-009 path: a prose ## T-NNN: roadmap must vouch a
        # stale archived plan's completion (table-only roadmap_status returned
        # None here before, blocking the dep and forcing a hand-replicated flow).
        _write(self.root / "docs/changes/archive/T-904/plan.md", _plan("T-904", "in-progress"))
        _write(self.root / "docs/roadmap.md",
               _roadmap_prose([("T-904", "completed (2026-07-05)")]))
        self.assertIn("READY", self._pf("T-904", OK).stdout)

    def test_archived_deferred_and_roadmap_deferred_blocks(self):
        _write(self.root / "docs/changes/archive/T-901/plan.md", _plan("T-901", "deferred"))
        _write(self.root / "docs/roadmap.md", _roadmap([("T-901", "deferred")]))
        self._pf("T-901", DEP)

    def test_active_inprogress_plan_stays_authoritative(self):
        # NOT archived -> the live body wins; still blocked even though roadmap says done.
        _write(self.root / "docs/changes/T-902/plan.md", _plan("T-902", "in-progress"))
        _write(self.root / "docs/roadmap.md", _roadmap([("T-902", "completed")]))
        self._pf("T-902", DEP)

    def test_archived_no_roadmap_row_trusts_body(self):
        # Archived but no roadmap vouches completion -> archive presence alone is
        # too weak (could be a removed deferred plan), so the body still blocks.
        _write(self.root / "docs/changes/archive/T-903/plan.md", _plan("T-903", "in-progress"))
        _write(self.root / "docs/roadmap.md", "# Roadmap\n")
        self._pf("T-903", DEP)

    # --- migration (Req 3) ---
    def test_migration_repairs_stale_skips_deferred_idempotent(self):
        _write(self.root / "docs/changes/archive/T-900/plan.md", _plan("T-900", "in-progress"))
        _write(self.root / "docs/changes/archive/T-901/plan.md", _plan("T-901", "deferred"))
        _write(self.root / "docs/roadmap.md",
               _roadmap([("T-900", "completed"), ("T-901", "deferred")]))
        out = self._mig().stdout
        self.assertIn("T-900", out)
        self.assertNotIn("T-901", out)  # roadmap not completed -> left alone
        self.assertIn("status: done",
                      (self.root / "docs/changes/archive/T-900/plan.md").read_text())
        self.assertIn("status: deferred",
                      (self.root / "docs/changes/archive/T-901/plan.md").read_text())
        # idempotent: a second run changes nothing
        self.assertIn("nothing to change", self._mig().stdout)

    def test_migration_dry_run_writes_nothing(self):
        _write(self.root / "docs/changes/archive/T-900/plan.md", _plan("T-900", "in-progress"))
        _write(self.root / "docs/roadmap.md", _roadmap([("T-900", "completed")]))
        self.assertIn("would bump", self._mig("--dry-run").stdout)
        self.assertIn("status: in-progress",
                      (self.root / "docs/changes/archive/T-900/plan.md").read_text())


class GitRefClaimTests(unittest.TestCase):
    """Tests for the git-ref distributed locking path (T-056).

    Each test sets up a bare "remote" + a local clone so the push path is
    exercised against a real git remote (a local bare repo). --no-push is
    NOT passed here — these tests specifically exercise the network path.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

        # Bare remote
        self.remote = self.tmp / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(self.remote)],
                       check=True)

        # Local clone A (the "first agent")
        self.local_a = self.tmp / "local_a"
        self.local_a.mkdir()
        _git(self.local_a, "init", "-q")
        _git(self.local_a, "config", "user.email", "t@t")
        _git(self.local_a, "config", "user.name", "t")
        (self.local_a / "f.txt").write_text("x")
        _git(self.local_a, "add", "-A")
        _git(self.local_a, "commit", "-qm", "init")
        _git(self.local_a, "branch", "-M", "main")
        _git(self.local_a, "remote", "add", "origin", str(self.remote))
        _git(self.local_a, "push", "-q", "origin", "main")

        # Local clone B (the "second agent" — different machine simulation)
        self.local_b = self.tmp / "local_b"
        subprocess.run(
            ["git", "clone", "-q", str(self.remote), str(self.local_b)],
            check=True,
        )
        _git(self.local_b, "config", "user.email", "t@t")
        _git(self.local_b, "config", "user.name", "t")

        self.cdir_a = self.tmp / "claims_a"
        self.cdir_b = self.tmp / "claims_b"

    def tearDown(self):
        self._tmp.cleanup()

    def _claim(self, local, cdir, task, session, touches="src/", expect=None):
        cmd = [
            sys.executable, str(SCRIPT),
            "claim",
            "--task-id", task,
            "--session-id", session,
            "--branch", f"feature/{task}",
            "--worktree", str(local),
            "--touches", touches,
            "--depends-on", "",
            "--claims-dir", str(cdir),
            # do NOT pass --no-push here — we want the real push path
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(local))
        if expect is not None:
            assert proc.returncode == expect, (
                f"expected exit {expect}, got {proc.returncode}\n"
                f"stdout={proc.stdout}\nstderr={proc.stderr}"
            )
        return proc

    def _release(self, local, cdir, task):
        cmd = [
            sys.executable, str(SCRIPT),
            "release",
            "--task-id", task,
            "--claims-dir", str(cdir),
            # do NOT pass --no-push
        ]
        return subprocess.run(cmd, capture_output=True, text=True, cwd=str(local))

    # --- no-push still works (local only) --------------------------------
    def test_no_push_claim_local_only(self):
        """--no-push must succeed without any remote interaction."""
        # Use a directory that is NOT a git repo to prove no git calls happen.
        non_repo = self.tmp / "non_repo"
        non_repo.mkdir()
        cdir = self.tmp / "claims_nopush"
        cmd = [
            sys.executable, str(SCRIPT),
            "claim",
            "--task-id", "T-200",
            "--session-id", "S-local",
            "--branch", "feature/T-200",
            "--worktree", str(non_repo),
            "--touches", "src/foo/",
            "--depends-on", "",
            "--claims-dir", str(cdir),
            "--no-push",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == OK, (
            f"--no-push claim failed: {proc.stdout}\n{proc.stderr}"
        )
        self.assertTrue((cdir / "T-200.json").exists())
        data = json.loads((cdir / "T-200.json").read_text())
        self.assertEqual(data["task_id"], "T-200")
        self.assertEqual(data["session_id"], "S-local")

    # --- first agent claims, second agent is blocked ---------------------
    def test_second_agent_blocked_when_ref_exists(self):
        """Agent B must be refused when Agent A already pushed a claim ref."""
        # Agent A claims first
        self._claim(self.local_a, self.cdir_a, "T-300", "S-A", expect=OK)
        # Verify the ref landed on the remote
        ls = subprocess.run(
            ["git", "ls-remote", str(self.remote), "refs/openup/claims/T-300"],
            capture_output=True, text=True,
        )
        self.assertIn("refs/openup/claims/T-300", ls.stdout,
                      "claim ref must be on the remote after agent A claims")

        # Agent B tries to claim the same task — must be refused
        proc_b = self._claim(self.local_b, self.cdir_b, "T-300", "S-B", expect=OWNER)
        self.assertIn("S-A", proc_b.stderr,
                      "error message must name the owning session")

        # Agent B's local claim file must NOT exist (rolled back)
        self.assertFalse((self.cdir_b / "T-300.json").exists(),
                         "local claim file must be rolled back on push rejection")

    # --- release deletes the remote ref ----------------------------------
    def test_release_deletes_remote_ref(self):
        """Releasing a claim must delete the ref on the remote."""
        self._claim(self.local_a, self.cdir_a, "T-301", "S-A", expect=OK)
        # Confirm ref is on remote
        ls_before = subprocess.run(
            ["git", "ls-remote", str(self.remote), "refs/openup/claims/T-301"],
            capture_output=True, text=True,
        )
        self.assertIn("T-301", ls_before.stdout)

        self._release(self.local_a, self.cdir_a, "T-301")

        ls_after = subprocess.run(
            ["git", "ls-remote", str(self.remote), "refs/openup/claims/T-301"],
            capture_output=True, text=True,
        )
        self.assertNotIn("T-301", ls_after.stdout,
                         "claim ref must be deleted from remote after release")

    # --- after release, second agent can claim ---------------------------
    def test_second_agent_can_claim_after_release(self):
        """Once agent A releases, agent B must be able to claim."""
        self._claim(self.local_a, self.cdir_a, "T-302", "S-A", expect=OK)
        self._release(self.local_a, self.cdir_a, "T-302")
        # Agent B can now claim (fetch + push should succeed)
        self._claim(self.local_b, self.cdir_b, "T-302", "S-B", expect=OK)
        data = json.loads((self.cdir_b / "T-302.json").read_text())
        self.assertEqual(data["session_id"], "S-B")


if __name__ == "__main__":
    unittest.main()
